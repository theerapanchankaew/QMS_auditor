#!/usr/bin/env python3
"""
evaluate_model_predictions.py — QMS Auditor v1.1
Evaluate model_predictions.jsonl against hidden gold answer key.

v1.1 changes (harness audit remediation):
  - Gold field assertion: warns loudly when gold uses alias fields instead of canonical "verdict"/"nc_class".
  - failure_layer inference: every error row now carries a predicted failure_layer (L4–L11) for
    targeted upskill routing.
  - Report includes failure_layer breakdown table.

Usage:
  python scripts/evaluate_model_predictions.py \
    --gold <gold_answer_key.jsonl> \
    --pred  model_predictions.jsonl \
    --outdir <results_dir>
"""
import argparse, json, csv
from datetime import datetime, timezone
from pathlib import Path

# ── Canonical gold field names ────────────────────────────────────────────────
GOLD_VERDICT_CANONICAL  = "verdict"
GOLD_NC_CLASS_CANONICAL = "nc_class"

# Accepted aliases (legacy support only — triggers assertion warning)
GOLD_VERDICT_ALIASES  = ["expected_verdict", "gold_verdict"]
GOLD_NC_CLASS_ALIASES = ["expected_nc_class", "gold_nc_class"]

# ── Prediction field names ────────────────────────────────────────────────────
PRED_VERDICT_FIELD  = "predicted_verdict"
PRED_NC_CLASS_FIELD = "predicted_nc_class"

# ── Verdict sets for failure_layer inference ──────────────────────────────────
NC_VERDICTS      = {"Noncomplied"}
ISSUE_VERDICTS   = {"Noncomplied", "OFI", "OBS", "InsufficientEvidence", "ReviewRequired"}
MAJOR_NC         = "Major"
MINOR_NC         = "Minor"


def load_jsonl(path):
    rows = []
    for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            r = json.loads(line)
            r["__line__"] = i
            rows.append(r)
    return rows


def norm_nc(x):
    if x is None:
        return "None"
    s = str(x).strip()
    return "None" if s in {"", "NA", "N/A", "null", "None"} else s


def assert_gold_fields(gold_records: list) -> list[str]:
    """
    P2 fix: verify gold file uses canonical field names.
    Returns list of warning strings (empty = all good).
    """
    warnings = []
    alias_hits = {a: 0 for a in GOLD_VERDICT_ALIASES + GOLD_NC_CLASS_ALIASES}
    canonical_verdict_missing = 0
    canonical_nc_missing = 0

    for r in gold_records:
        if GOLD_VERDICT_CANONICAL not in r:
            canonical_verdict_missing += 1
            for a in GOLD_VERDICT_ALIASES:
                if a in r:
                    alias_hits[a] += 1
        if GOLD_NC_CLASS_CANONICAL not in r:
            canonical_nc_missing += 1
            for a in GOLD_NC_CLASS_ALIASES:
                if a in r:
                    alias_hits[a] += 1

    if canonical_verdict_missing > 0:
        warnings.append(
            f"GOLD_FIELD_WARNING: {canonical_verdict_missing} gold records missing "
            f"canonical field '{GOLD_VERDICT_CANONICAL}'. "
            f"Alias hits: {dict((k,v) for k,v in alias_hits.items() if v > 0)}. "
            f"Gold files SHOULD use '{GOLD_VERDICT_CANONICAL}' (not expected_verdict/gold_verdict). "
            f"Falling back to alias resolution for this run."
        )
    if canonical_nc_missing > 0:
        warnings.append(
            f"GOLD_FIELD_WARNING: {canonical_nc_missing} gold records missing "
            f"canonical field '{GOLD_NC_CLASS_CANONICAL}'. "
            f"Gold files SHOULD use '{GOLD_NC_CLASS_CANONICAL}' (not expected_nc_class/gold_nc_class). "
            f"Falling back to alias resolution for this run."
        )
    return warnings


def pick_gold_verdict(row):
    """Pick verdict from gold record — canonical first, then aliases."""
    if GOLD_VERDICT_CANONICAL in row:
        return row[GOLD_VERDICT_CANONICAL]
    for alias in GOLD_VERDICT_ALIASES:
        if alias in row:
            return row[alias]
    return None


def pick_gold_nc(row):
    """Pick nc_class from gold record — canonical first, then aliases."""
    if GOLD_NC_CLASS_CANONICAL in row:
        return row[GOLD_NC_CLASS_CANONICAL]
    for alias in GOLD_NC_CLASS_ALIASES:
        if alias in row:
            return row[alias]
    return None


def infer_failure_layer(gv, pv, gnc, pnc) -> str:
    """
    P1 fix: infer the most likely cognition layer that caused the mismatch.

    Layer attribution rules (from references/28-evidence-schema.md §4):
      OFI vs Noncomplied (either direction) → L7 (conditional qualifier gate)
      Major vs Minor mismatch (same Noncomplied verdict) → L9/L10 (exposure/severity)
      Complied vs InsufficientEvidence or vice versa → L4 (evidence parser)
      Complied vs OFI → L6/L11 (element decomposition / counterfactual)
      Noncomplied vs Complied (FP or FN) → L8 (breach test) — generic
      Wrong clause (if available) → L5 (clause mapper) — checked by caller if data available
      Any NC class mismatch without verdict mismatch → L10/L11 (severity/counterfactual)
    """
    if gv == pv and gnc != pnc and gv == "Noncomplied":
        return "L10_L11_severity_counterfactual"

    if gv == pv:
        return "none"

    ofi_nc_pair = {frozenset(["OFI", "Noncomplied"])}
    if frozenset([gv, pv]) in ofi_nc_pair:
        return "L7_conditional_qualifier"

    if "InsufficientEvidence" in (gv, pv) and "Complied" in (gv, pv):
        return "L4_evidence_parser"

    if "OFI" in (gv, pv) and "Complied" in (gv, pv):
        return "L6_L11_element_or_counterfactual"

    if "OBS" in (gv, pv) and "Noncomplied" in (gv, pv):
        return "L8_breach_test"

    if gv == "Noncomplied" and pv == "Complied":
        return "L8_breach_test_FN"

    if gv == "Complied" and pv == "Noncomplied":
        return "L8_breach_test_FP"

    if gv in NC_VERDICTS and pv in NC_VERDICTS and gnc != pnc:
        return "L10_L11_severity_counterfactual"

    return "L_unclassified"


def f1_metrics(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    rows = []
    for lab in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec  = tp / (tp + fn) if tp + fn else 0.0
        f1   = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        sup  = sum(1 for t in y_true if t == lab)
        rows.append({"class": lab, "precision": prec, "recall": rec, "f1": f1,
                     "support": sup, "tp": tp, "fp": fp, "fn": fn})
    n       = len(y_true)
    acc     = sum(1 for t, p in zip(y_true, y_pred) if t == p) / n if n else 0
    macro   = sum(r["f1"] for r in rows) / len(rows) if rows else 0
    weighted = sum(r["f1"] * r["support"] for r in rows) / n if n else 0
    return {"accuracy": acc, "micro_f1": acc, "macro_f1": macro,
            "weighted_f1": weighted, "per_class": rows}


def main():
    p = argparse.ArgumentParser(
        description="Evaluate QMS model_predictions.jsonl against hidden gold answer key.")
    p.add_argument("--gold",   required=True)
    p.add_argument("--pred",   required=True)
    p.add_argument("--outdir", required=True)
    args = p.parse_args()
    out  = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    gold = load_jsonl(args.gold)
    pred = load_jsonl(args.pred)

    # ── P2: Gold field assertion ─────────────────────────────────────────────
    gold_warnings = assert_gold_fields(gold)
    for w in gold_warnings:
        print(f"[ASSERTION] {w}")

    g  = {r["case_id"]: r for r in gold if r.get("case_id")}
    pr = {r["case_id"]: r for r in pred if r.get("case_id")}

    ids     = sorted(set(g) & set(pr))
    missing = sorted(set(g) - set(pr))
    extra   = sorted(set(pr) - set(g))

    # ── Build target arrays ──────────────────────────────────────────────────
    targets = {}
    targets["verdict"] = (
        [pick_gold_verdict(g[i]) for i in ids],
        [pr[i].get(PRED_VERDICT_FIELD) or pr[i].get("verdict") for i in ids],
    )
    targets["nc_class"] = (
        [norm_nc(pick_gold_nc(g[i])) for i in ids],
        [norm_nc(pr[i].get(PRED_NC_CLASS_FIELD) or pr[i].get("nc_class")) for i in ids],
    )
    targets["composite_verdict_nc"] = (
        [f"{targets['verdict'][0][j]}+{targets['nc_class'][0][j]}" for j in range(len(ids))],
        [f"{targets['verdict'][1][j]}+{targets['nc_class'][1][j]}" for j in range(len(ids))],
    )

    has_clause = any(
        (g[i].get("expected_clause") or g[i].get("clause") or g[i].get("gold_clause")) is not None
        or (pr[i].get("predicted_clause") or pr[i].get("clause")) is not None
        for i in ids
    )
    if has_clause:
        targets["clause"] = (
            [str(g[i].get("expected_clause") or g[i].get("clause") or g[i].get("gold_clause", "")) for i in ids],
            [str(pr[i].get("predicted_clause") or pr[i].get("clause", "")) for i in ids],
        )

    # ── F1 summary ───────────────────────────────────────────────────────────
    summary = []
    per     = []
    for name, (yt, yp) in targets.items():
        m = f1_metrics(yt, yp)
        summary.append({"target": name,
                         **{k: m[k] for k in ["accuracy", "micro_f1", "macro_f1", "weighted_f1"]}})
        for r in m["per_class"]:
            per.append({"target": name, **r})

    with open(out / "metric_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["target", "accuracy", "micro_f1", "macro_f1", "weighted_f1"])
        w.writeheader(); w.writerows(summary)

    with open(out / "per_class_metrics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["target", "class", "precision", "recall", "f1",
                                           "support", "tp", "fp", "fn"])
        w.writeheader(); w.writerows(per)

    # ── P1: Error analysis with failure_layer ────────────────────────────────
    errors = []
    layer_counts: dict[str, int] = {}
    for i in ids:
        gv  = pick_gold_verdict(g[i])
        pv  = pr[i].get(PRED_VERDICT_FIELD) or pr[i].get("verdict")
        gnc = norm_nc(pick_gold_nc(g[i]))
        pnc = norm_nc(pr[i].get(PRED_NC_CLASS_FIELD) or pr[i].get("nc_class"))
        if gv != pv or gnc != pnc:
            layer = infer_failure_layer(gv, pv, gnc, pnc)
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
            errors.append({
                "case_id":            i,
                "gold_verdict":       gv,
                "predicted_verdict":  pv,
                "gold_nc_class":      gnc,
                "predicted_nc_class": pnc,
                "failure_layer":      layer,
            })

    with open(out / "error_analysis.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "gold_verdict", "predicted_verdict",
                                           "gold_nc_class", "predicted_nc_class", "failure_layer"])
        w.writeheader(); w.writerows(errors)

    # ── Failure-layer breakdown ───────────────────────────────────────────────
    layer_rows = [{"failure_layer": k, "count": v,
                   "upskill_action": _layer_to_upskill(k)}
                  for k, v in sorted(layer_counts.items(), key=lambda x: -x[1])]
    with open(out / "failure_layer_breakdown.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["failure_layer", "count", "upskill_action"])
        w.writeheader(); w.writerows(layer_rows)

    # ── Missing / extra predictions ───────────────────────────────────────────
    (out / "missing_predictions.txt").write_text("\n".join(missing), encoding="utf-8")
    (out / "extra_predictions.txt").write_text("\n".join(extra),   encoding="utf-8")

    # ── Performance report ────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    report  = "# QMS Model Performance Report\n\n"
    report += "Evaluation type: real model performance only if predictions were generated "
    report += "from sanitized inputs and gold was hidden from model.\n\n"
    if gold_warnings:
        report += "## Gold field warnings\n\n"
        for w in gold_warnings:
            report += f"- {w}\n"
        report += "\n"
    report += (f"- Generated: {now}\n"
               f"- Gold records: {len(gold)}\n"
               f"- Prediction records: {len(pred)}\n"
               f"- Matched case_id: {len(ids)}\n"
               f"- Missing predictions: {len(missing)}\n"
               f"- Extra predictions: {len(extra)}\n"
               f"- Verdict/NC errors: {len(errors)}\n\n")

    report += "## Metric summary\n\n"
    report += "| Target | Accuracy | Micro F1 | Macro F1 | Weighted F1 |\n|---|---:|---:|---:|---:|\n"
    for s in summary:
        report += (f"| {s['target']} | {s['accuracy']:.4f} | {s['micro_f1']:.4f} "
                   f"| {s['macro_f1']:.4f} | {s['weighted_f1']:.4f} |\n")

    if layer_rows:
        report += "\n## Failure layer breakdown (upskill routing)\n\n"
        report += "| Layer | Errors | Upskill action |\n|---|---:|---|\n"
        for r in layer_rows:
            report += f"| `{r['failure_layer']}` | {r['count']} | {r['upskill_action']} |\n"

    (out / "performance_report.md").write_text(report, encoding="utf-8")

    result = {
        "status":          "passed",
        "matched":         len(ids),
        "missing":         len(missing),
        "extra":           len(extra),
        "errors":          len(errors),
        "gold_warnings":   len(gold_warnings),
        "failure_layers":  layer_counts,
        "outdir":          str(out),
    }
    print(json.dumps(result, indent=2))


def _layer_to_upskill(layer: str) -> str:
    return {
        "L7_conditional_qualifier":         "Re-read ref/26 L7; enforce OFI-before-NC for conditional clauses",
        "L8_breach_test":                   "Re-read ref/26 L8; require all 4 breach elements",
        "L8_breach_test_FN":                "Re-read ref/26 L8; check missed breach evidence (False Negative)",
        "L8_breach_test_FP":                "Re-read ref/26 L8; check over-eager NC (False Positive)",
        "L9_L10_severity_counterfactual":   "Re-read ref/26 L9-L11; enforce M-trigger + counterfactual",
        "L10_L11_severity_counterfactual":  "Re-read ref/26 L10-L11; enforce D-anchor + counterfactual",
        "L4_evidence_parser":               "Re-read ref/26 L4; enforce implementation_proven check",
        "L6_L11_element_or_counterfactual": "Re-read ref/26 L6+L11; element decomposition + Complied challenge",
        "L_unclassified":                   "Manual review required; pattern not matched by auto-attribution",
    }.get(layer, "Manual review")


if __name__ == "__main__":
    main()
