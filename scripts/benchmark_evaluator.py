#!/usr/bin/env python3
"""
benchmark_evaluator.py — QMS Auditor v1 Benchmark Evaluator
Purpose: Score AI-generated QMS audit output against a JSONL answer key.
         Enforces strict source role separation (GT = JSONL, PRED = report).
         Outputs a Consolidated Audit Evaluation Report in markdown.
Usage:
  python scripts/benchmark_evaluator.py
    --answer-key <path_to_answer_key.jsonl>
    --prediction  <path_to_generated_report.jsonl or .md>
    [--output     <output_report.md>]
    [--mode       strict | relaxed]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from collections import defaultdict

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BUNDLE_ROOT = os.path.dirname(SCRIPT_DIR)

# ── Ground Truth field names (JSONL only) ────────────────────────────────────
GT_VERDICT_FIELD  = "verdict"
GT_NC_CLASS_FIELD = "nc_class"
GT_ID_FIELD       = "case_id"

# ── Prediction field names (report only) ─────────────────────────────────────
PRED_VERDICT_FIELD  = "generated_verdict"
PRED_NC_CLASS_FIELD = "generated_nc_class"
PRED_ID_FIELD       = "case_id"

# ── Forbidden: report fields that must NEVER be used as GT ───────────────────
FORBIDDEN_AS_GT = ["expected_verdict", "expected_nc_class", "expected_nc_class_field"]


def normalize_verdict(v) -> str:
    if v is None or str(v).strip() in ("", "None", "N/A", "NA", "nan"):
        return "Unknown"
    v = str(v).strip().lower()
    mapping = {
        "complied": "Complied", "noncomplied": "Noncomplied",
        "ofi": "OFI", "obs": "OBS",
        "insufficientevidence": "InsufficientEvidence",
        "reviewrequired": "ReviewRequired",
        "out_of_scope": "OUT_OF_SCOPE",
        "referencegap": "ReferenceGap",
    }
    return mapping.get(v, "Unknown")


def normalize_nc_class(v) -> str:
    if v is None or str(v).strip() in ("", "None", "N/A", "NA", "nan", "null"):
        return "None"
    v = str(v).strip().lower()
    if v == "major":
        return "Major"
    if v == "minor":
        return "Minor"
    return "Unknown"


def binary(verdict: str) -> str:
    """Collapse verdict to binary: Noncomplied vs Complied."""
    if verdict in ("Noncomplied",):
        return "Noncomplied"
    if verdict in ("Complied",):
        return "Complied"
    return "Noncomplied"  # OFI/OBS/InsufficientEvidence treated as non-positive for strict binary


def load_jsonl(path: str, id_field: str, verdict_field: str, nc_class_field: str,
               is_gt: bool) -> dict:
    """Load JSONL file; enforce field name contract."""
    records = {}
    errors  = []

    if not os.path.exists(path):
        print(json.dumps({"status": "BENCHMARK_SOURCE_ERROR",
                          "error": f"File not found: {path}"}))
        sys.exit(2)

    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: JSON decode error — {e}")
                continue

            # ── Enforce forbidden GT fields in PRED ────────────────────────
            if not is_gt:
                for forbidden in FORBIDDEN_AS_GT:
                    if forbidden in rec:
                        errors.append(
                            f"BENCHMARK_FIELD_ERROR at line {i}: "
                            f"report contains '{forbidden}' — this must NOT be used as GT. "
                            f"Use only '{PRED_VERDICT_FIELD}' and '{PRED_NC_CLASS_FIELD}'."
                        )

            case_id = rec.get(id_field)
            if not case_id:
                errors.append(f"Line {i}: missing '{id_field}' — skipped")
                continue

            verdict  = normalize_verdict(rec.get(verdict_field))
            nc_class = normalize_nc_class(rec.get(nc_class_field))
            records[str(case_id)] = {"case_id": str(case_id), "verdict": verdict, "nc_class": nc_class}

    if errors:
        for e in errors:
            print(f"[LOAD WARNING] {e}", file=sys.stderr)

    return records


def safe_f1(tp, fp, fn) -> float | str:
    if (tp + fp) == 0 or (tp + fn) == 0:
        return "insufficient_data"
    precision = tp / (tp + fp)
    recall    = tp / (tp + fn)
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def compute_metrics(cases: list[dict]) -> dict:
    """Compute all 4-dimensional metrics from joined case list."""
    tp = fp = fn = tn = 0
    verdict_correct = 0
    nc_strict_correct = nc_strict_total = 0
    nc_overall_correct = 0

    failed = []
    by_clause: dict = defaultdict(lambda: {"correct": 0, "total": 0})

    for c in cases:
        gt_v  = c["gt_verdict"]
        pr_v  = c["pred_verdict"]
        gt_nc = c["gt_nc_class"]
        pr_nc = c["pred_nc_class"]

        # ── Binary F1 ─────────────────────────────────────────────────────
        gt_bin = "Noncomplied" if gt_v == "Noncomplied" else "Complied"
        pr_bin = "Noncomplied" if pr_v == "Noncomplied" else "Complied"
        if gt_bin == "Noncomplied" and pr_bin == "Noncomplied": tp += 1
        elif gt_bin == "Complied"  and pr_bin == "Noncomplied": fp += 1
        elif gt_bin == "Noncomplied" and pr_bin == "Complied":  fn += 1
        else: tn += 1

        # ── Verdict accuracy ───────────────────────────────────────────────
        if gt_v == pr_v:
            verdict_correct += 1

        # ── NC class accuracy ──────────────────────────────────────────────
        if gt_nc in ("Major", "Minor"):
            nc_strict_total += 1
            if pr_nc == gt_nc:
                nc_strict_correct += 1

        # Overall NC class (None==None for Complied cases)
        if (gt_nc in ("Major", "Minor") and pr_nc == gt_nc) or \
           (gt_nc == "None" and pr_nc == "None"):
            nc_overall_correct += 1

        # ── Clause-level tracking ─────────────────────────────────────────
        clause = c.get("clause", "unknown")
        by_clause[clause]["total"] += 1
        if gt_v == pr_v:
            by_clause[clause]["correct"] += 1

        # ── Failed cases ──────────────────────────────────────────────────
        if gt_v != pr_v:
            if gt_bin == "Complied" and pr_bin == "Noncomplied":
                failure_type = "FP"
            elif gt_bin == "Noncomplied" and pr_bin == "Complied":
                failure_type = "FN"
            elif gt_v != pr_v:
                failure_type = "verdict_mismatch"
            else:
                failure_type = "nc_class_mismatch"
            failed.append({
                "case_id":    c["case_id"],
                "gt_verdict": gt_v,
                "pred_verdict": pr_v,
                "gt_nc_class": gt_nc,
                "pred_nc_class": pr_nc,
                "failure_type": failure_type
            })
        elif gt_nc in ("Major", "Minor") and pr_nc != gt_nc:
            failed.append({
                "case_id":    c["case_id"],
                "gt_verdict": gt_v,
                "pred_verdict": pr_v,
                "gt_nc_class": gt_nc,
                "pred_nc_class": pr_nc,
                "failure_type": "nc_class_mismatch"
            })

    n = len(cases)
    binary_f1 = safe_f1(tp, fp, fn)

    return {
        "total":       n,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "binary_f1":  binary_f1,
        "binary_precision": round(tp/(tp+fp), 4) if (tp+fp) > 0 else "insufficient_data",
        "binary_recall":    round(tp/(tp+fn), 4) if (tp+fn) > 0 else "insufficient_data",
        "verdict_accuracy": round(verdict_correct / n * 100, 1) if n else 0,
        "verdict_correct":  verdict_correct,
        "strict_nc_accuracy": round(nc_strict_correct / nc_strict_total * 100, 1) if nc_strict_total else 0,
        "strict_nc_total":   nc_strict_total,
        "overall_nc_accuracy": round(nc_overall_correct / n * 100, 1) if n else 0,
        "failed_cases":  failed,
        "failed_count":  len(failed),
        "clause_accuracy": {
            k: {
                "accuracy": round(v["correct"] / v["total"] * 100, 1),
                "correct": v["correct"],
                "total": v["total"]
            }
            for k, v in sorted(by_clause.items())
        }
    }


def build_report(gt: dict, pred: dict, gt_path: str, pred_path: str,
                 metrics: dict, cases: list) -> str:
    now = datetime.now(timezone.utc).isoformat()

    gt_complied   = sum(1 for c in cases if c["gt_verdict"] == "Complied")
    gt_nc         = sum(1 for c in cases if c["gt_verdict"] == "Noncomplied")
    gt_major      = sum(1 for c in cases if c["gt_nc_class"] == "Major")
    gt_minor      = sum(1 for c in cases if c["gt_nc_class"] == "Minor")
    pred_complied = sum(1 for c in cases if c["pred_verdict"] == "Complied")
    pred_nc       = sum(1 for c in cases if c["pred_verdict"] == "Noncomplied")

    # Failed cases table
    fc_rows = ""
    for fc in metrics["failed_cases"]:
        fc_rows += (
            f"| {fc['case_id']} | {fc['gt_verdict']} | {fc['pred_verdict']} "
            f"| {fc['gt_nc_class']} | {fc['pred_nc_class']} | {fc['failure_type']} |\n"
        )
    if not fc_rows:
        fc_rows = "| — | — | — | — | — | — |\n"

    # Clause accuracy
    clause_rows = ""
    for clause, ca in metrics["clause_accuracy"].items():
        clause_rows += f"| {clause} | {ca['accuracy']}% | {ca['correct']} / {ca['total']} |\n"

    report = f"""# Consolidated QMS Audit Evaluation Report
> Standard: ISO 9001:2026 | Mode: BENCHMARK_MODE | Generated: {now}

---

## 1. Source Verification
| Item | Value |
|---|---|
| GT source | {os.path.basename(gt_path)} |
| GT fields used | `{GT_VERDICT_FIELD}`, `{GT_NC_CLASS_FIELD}` |
| PRED source | {os.path.basename(pred_path)} |
| PRED fields used | `{PRED_VERDICT_FIELD}`, `{PRED_NC_CLASS_FIELD}` |
| Total GT cases | {len(gt)} |
| Total PRED cases | {len(pred)} |
| Cases after join | {len(cases)} |

---

## 2. Case Distribution
| Category | Count |
|---|---|
| Total test cases | {metrics['total']} |
| GT Complied | {gt_complied} |
| GT Noncomplied | {gt_nc} |
| — GT Major NC | {gt_major} |
| — GT Minor NC | {gt_minor} |
| PRED Complied | {pred_complied} |
| PRED Noncomplied | {pred_nc} |

---

## 3. Accuracy Metrics
| Metric | Value |
|---|---|
| Verdict Accuracy | {metrics['verdict_accuracy']}% ({metrics['verdict_correct']}/{metrics['total']}) |
| Strict NC Classification Accuracy | {metrics['strict_nc_accuracy']}% ({metrics['strict_nc_total']} cases with GT Major/Minor) |
| Overall NC Classification Accuracy | {metrics['overall_nc_accuracy']}% |
| F1 Score | {metrics['binary_f1']} |
| Precision | {metrics['binary_precision']} |
| Recall | {metrics['binary_recall']} |
| Total Failed Cases | {metrics['failed_count']} |

---

## 4. Confusion Matrix
| | PRED Complied | PRED Noncomplied |
|---|---|---|
| **GT Complied** | TN = {metrics['tn']} | FP = {metrics['fp']} |
| **GT Noncomplied** | FN = {metrics['fn']} | TP = {metrics['tp']} |

---

## 5. Clause-Level Accuracy
| Clause | Accuracy | Correct / Total |
|---|---|---|
{clause_rows}
---

## 6. Failed Cases ({metrics['failed_count']} total)
| case_id | GT verdict | PRED verdict | GT nc_class | PRED nc_class | Failure type |
|---|---|---|---|---|---|
{fc_rows}
---

## 7. Source Integrity Declaration
- GT fields used: `{GT_VERDICT_FIELD}`, `{GT_NC_CLASS_FIELD}` from JSONL answer key ✓
- PRED fields used: `{PRED_VERDICT_FIELD}`, `{PRED_NC_CLASS_FIELD}` from generated report ✓
- No `expected_*` columns from report used as GT: CONFIRMED ✓
- No re-derivation of verdicts from evidence performed: CONFIRMED ✓
- NC class normalization applied (blank/None/N/A → None): CONFIRMED ✓
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="QMS Benchmark Evaluator")
    parser.add_argument("--answer-key",  type=str, required=True)
    parser.add_argument("--prediction",  type=str, required=True)
    parser.add_argument("--output",      type=str, default="")
    parser.add_argument("--mode",        type=str, default="strict",
                        choices=["strict","relaxed"])
    args = parser.parse_args()

    # ── Pre-computation checklist ────────────────────────────────────────────
    print("[CHECKLIST] 1. Loading GT source ...", file=sys.stderr)
    gt = load_jsonl(args.answer_key, GT_ID_FIELD, GT_VERDICT_FIELD, GT_NC_CLASS_FIELD, is_gt=True)

    print("[CHECKLIST] 2. Loading PRED source ...", file=sys.stderr)
    pred = load_jsonl(args.prediction, PRED_ID_FIELD, PRED_VERDICT_FIELD, PRED_NC_CLASS_FIELD, is_gt=False)

    print(f"[CHECKLIST] 3. GT={len(gt)} cases, PRED={len(pred)} cases", file=sys.stderr)

    # ── Join on case_id ──────────────────────────────────────────────────────
    joined_ids  = set(gt.keys()) & set(pred.keys())
    dropped_gt  = set(gt.keys()) - joined_ids
    dropped_pred= set(pred.keys()) - joined_ids

    if dropped_gt or dropped_pred:
        print(f"[CHECKLIST] BENCHMARK_JOIN_WARNING: {len(dropped_gt)} GT-only, "
              f"{len(dropped_pred)} PRED-only cases dropped.", file=sys.stderr)

    cases = []
    for cid in sorted(joined_ids):
        g = gt[cid]; p = pred[cid]
        cases.append({
            "case_id":    cid,
            "gt_verdict":   g["verdict"],
            "gt_nc_class":  g["nc_class"],
            "pred_verdict": p["verdict"],
            "pred_nc_class": p["nc_class"],
            "clause":     gt[cid].get("clause", "unknown")
        })

    print(f"[CHECKLIST] 4–8. {len(cases)} cases joined. Computing metrics ...", file=sys.stderr)

    metrics = compute_metrics(cases)
    report  = build_report(gt, pred, args.answer_key, args.prediction, metrics, cases)

    print(report)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n[OUTPUT] Report written to: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Could not write output: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
