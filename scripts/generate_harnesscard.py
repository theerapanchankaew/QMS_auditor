#!/usr/bin/env python3
"""
generate_harnesscard.py — QMS Auditor v1.1
Generate HarnessCard report with live telemetry from f1_stats.json and last regression.

v1.1 changes (harness audit remediation):
  - Embeds last_f1, last_regression_date, regression_status from live stats files.
  - Reports failing layers from most recent behavioral regression run.
  - HarnessCard is no longer purely static — it reflects current skill health.

Usage:
  python scripts/generate_harnesscard.py --skill-root . --out harnesscard-report.md
"""
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_FILES = [
    "SKILL.md",
    "references/29-harnesscard-qms-auditor.md",
    "references/30-control-layer-contract.md",
    "references/31-agency-action-surface.md",
    "references/32-context-window-management.md",
    "references/33-runtime-recovery-and-repeatability.md",
    "references/34-evaluation-harness-protocol.md",
    "references/35-robustness-test-suite.md",
    "assets/templates/context-ledger-template.json",
    "assets/templates/decision-trace-template.json",
    "assets/templates/model-predictions-schema.json",
    "scripts/run_regression_suite.py",
    "scripts/evaluate_model_predictions.py",
    "scripts/prepare_model_performance_inputs.py",
    # behavioral fixtures
    "assets/tests/behavioral-smoke-gold.jsonl",
    "assets/tests/behavioral-smoke-pred-pass.jsonl",
    "assets/tests/behavioral-smoke-pred-fail.jsonl",
]


def load_json_safe(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_last_regression(out_dir: Path) -> dict:
    """Load most recent regression_results.json from default output dir."""
    result_path = out_dir / "regression_results.json"
    data = load_json_safe(result_path)
    if not data:
        return {"status": "not_run", "passed": "N/A", "total": "N/A", "groups": {}}
    groups = data.get("groups", {})
    checks = data.get("checks", [])
    pass_count = sum(1 for c in checks if c.get("passed"))
    return {
        "status":     data.get("status", "unknown"),
        "passed":     pass_count,
        "total":      len(checks),
        "groups":     groups,
        "failing_checks": [
            {"check": c["check"], "target": c.get("target",""), "note": c.get("note","")}
            for c in checks if not c.get("passed")
        ],
    }


def load_f1_telemetry(f1_path: Path) -> dict:
    """Extract key F1 telemetry from f1_stats.json."""
    data = load_json_safe(f1_path)
    if not data:
        return {"available": False, "note": "f1_stats.json not found or empty"}
    overall_f1 = data.get("overall_f1")
    gen_at     = data.get("generated_at", "unknown")
    alerts     = data.get("alerts", [])
    # Pull per-route stats where data is available
    route_summary = {}
    for route, stats in data.get("by_route", {}).items():
        f1_val = stats.get("f1")
        n      = stats.get("n", 0)
        if n > 0 and f1_val is not None:
            route_summary[route] = {"f1": f1_val, "n": n,
                                    "status": stats.get("f1_status", "ok")}
    clause_summary = {}
    for clause, stats in data.get("by_clause_group", {}).items():
        f1_val = stats.get("f1")
        n      = stats.get("n", 0)
        if n > 0 and f1_val is not None:
            clause_summary[clause] = {"f1": f1_val, "n": n}
    return {
        "available":      True,
        "generated_at":   gen_at,
        "overall_f1":     overall_f1,
        "total_events":   data.get("total_feedback_events", 0),
        "alerts":         alerts,
        "by_route":       route_summary,
        "by_clause":      clause_summary,
    }


def main():
    p = argparse.ArgumentParser(description="Generate QMS auditor HarnessCard report v1.1")
    p.add_argument("--skill-root",  default=".")
    p.add_argument("--out",         default="harnesscard-report.md")
    p.add_argument("--regression-results-dir", default="regression_results",
                   help="Directory containing regression_results.json from last run_regression_suite run")
    args = p.parse_args()

    root      = Path(args.skill_root)
    out_path  = Path(args.out)
    reg_dir   = Path(args.regression_results_dir)
    now       = datetime.now(timezone.utc).isoformat()

    present = [f for f in REQUIRED_FILES if (root / f).exists()]
    missing = [f for f in REQUIRED_FILES if not (root / f).exists()]

    # ── Live telemetry ─────────────────────────────────────────────────────────
    f1_data  = load_f1_telemetry(root / "assets" / "stats" / "f1_stats.json")
    reg_data = load_last_regression(reg_dir)

    # ── Build HarnessCard ─────────────────────────────────────────────────────
    txt  = "# HarnessCard Report: QMS Auditor ISO 9001:2026 Hardened\n\n"
    txt += f"Generated: {now}\n\n"

    txt += "## Artifact inventory\n\n"
    txt += f"- Present hardened artifacts: {len(present)}/{len(REQUIRED_FILES)}\n"
    txt += f"- Missing hardened artifacts: {len(missing)}\n"
    txt += "- External sources used: false\n"
    txt += "- Source boundary: bundled skill files and user-uploaded controlled evidence only\n\n"

    if present:
        txt += "### Present artifacts\n" + "\n".join(f"- `{x}`" for x in present) + "\n\n"
    if missing:
        txt += "### Missing artifacts\n" + "\n".join(f"- `{x}`" for x in missing) + "\n\n"

    # ── Regression telemetry ──────────────────────────────────────────────────
    txt += "## Last regression run\n\n"
    if reg_data["status"] == "not_run":
        txt += "_No regression results found. Run:_ `python scripts/run_regression_suite.py --skill-root . --outdir regression_results`\n\n"
    else:
        txt += f"- Status: **{reg_data['status']}**\n"
        txt += f"- Checks passed: {reg_data['passed']}/{reg_data['total']}\n"
        if reg_data.get("groups"):
            txt += "\n| Group | Passed | Total |\n|---|---:|---:|\n"
            for g, counts in reg_data["groups"].items():
                txt += f"| {g} | {counts['passed']} | {counts['total']} |\n"
            txt += "\n"
        failing = reg_data.get("failing_checks", [])
        if failing:
            txt += "### Failing checks\n\n"
            for fc in failing:
                txt += f"- `{fc['check']}` on `{fc['target']}`: {fc['note']}\n"
            txt += "\n"

    # ── F1 telemetry ──────────────────────────────────────────────────────────
    txt += "## Operational F1 telemetry\n\n"
    if not f1_data["available"]:
        txt += "_F1 stats not available. Collect feedback via_ `scripts/feedback_collector.py`_.\n\n"
    else:
        overall = f1_data["overall_f1"]
        txt += f"- Last updated: {f1_data['generated_at']}\n"
        txt += f"- Total feedback events: {f1_data['total_events']}\n"
        txt += f"- Overall F1: {overall if overall is not None else 'insufficient_data'}\n\n"

        if f1_data["by_route"]:
            txt += "### F1 by route\n\n"
            txt += "| Route | F1 | Events | Status |\n|---|---:|---:|---|\n"
            for route, s in f1_data["by_route"].items():
                txt += f"| {route} | {s['f1']:.4f} | {s['n']} | {s['status']} |\n"
            txt += "\n"

        if f1_data["by_clause"]:
            txt += "### F1 by clause group\n\n"
            txt += "| Clause | F1 | Events |\n|---|---:|---:|\n"
            for clause, s in f1_data["by_clause"].items():
                txt += f"| {clause} | {s['f1']:.4f} | {s['n']} |\n"
            txt += "\n"

        if f1_data["alerts"]:
            txt += "### Active alerts\n\n"
            for alert in f1_data["alerts"]:
                txt += f"- {alert}\n"
            txt += "\n"

    txt += "## Primary operating model\n\n"
    txt += ("Control artifacts, agency/action surface, runtime policy, evaluation protocol, "
            "observability, and regression checks are explicit in the skill bundle. "
            "This HarnessCard reflects live telemetry from the last regression run and "
            "operational F1 feedback log.\n")

    out_path.write_text(txt, encoding="utf-8")
    print(json.dumps({
        "status":              "passed",
        "out":                 str(out_path),
        "present":             len(present),
        "missing":             missing,
        "regression_status":   reg_data["status"],
        "overall_f1":          f1_data.get("overall_f1"),
        "f1_telemetry_events": f1_data.get("total_events", 0),
    }, indent=2))


if __name__ == "__main__":
    main()
