#!/usr/bin/env python3
"""F1 tracker for QMS skill.

Reads assets/stats/feedback_log.jsonl and produces segmented F1 reports.
Outputs behavior adjustment recommendations for route strictness.

Usage:
  python scripts/f1_tracker.py --report
  python scripts/f1_tracker.py --report --route nc_classification
  python scripts/f1_tracker.py --report --clause-group 8.4
  python scripts/f1_tracker.py --reset-segment "route:nc_classification" --note "Major skill update"
  python scripts/f1_tracker.py --check-route nc_classification
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_LOG = SKILL_ROOT / "assets" / "stats" / "feedback_log.jsonl"
F1_STATS_OUT = SKILL_ROOT / "assets" / "stats" / "f1_stats.json"
F1_RESET_LOG = SKILL_ROOT / "assets" / "stats" / "f1_reset_log.jsonl"

MIN_SAMPLES = {"route": 10, "clause_group": 5, "verdict_type": 5}

ROUTES = [
    "nc_classification",
    "conformity_evaluation",
    "predictive_risk_scoring",
    "audit_workflow",
    "iso_clause_advisor",
    "full_ahp_evaluation",
]

CLAUSE_GROUPS = ["4", "5", "6", "7", "8", "8.4", "8.5", "9", "10"]

VERDICT_TYPES = ["Major", "Minor", "OBS", "OFI", "Complied", "InsufficientEvidence"]

# ---------------------------------------------------------------------------
# Load feedback
# ---------------------------------------------------------------------------

def load_feedback(exclude_sessions: list[str] | None = None) -> list[dict]:
    if not FEEDBACK_LOG.exists():
        return []
    records = []
    with FEEDBACK_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if exclude_sessions and r.get("session_id") in exclude_sessions:
                    continue
                records.append(r)
            except json.JSONDecodeError:
                pass
    return records


# ---------------------------------------------------------------------------
# F1 computation
# ---------------------------------------------------------------------------

def _f1_from_records(records: list[dict]) -> dict:
    tp = fp = fn = tn = partial = 0
    for r in records:
        label = r.get("f1_label", "skip")
        if label == "TP":
            tp += 1
        elif label == "FP":
            fp += 1
        elif label == "FN":
            fn += 1
        elif label == "TN":
            tn += 1
        elif label == "partial":
            partial += 1

    tp_eff = tp + 0.5 * partial
    fp_eff = fp + 0.5 * partial
    n = tp + fp + fn + tn + partial

    precision = tp_eff / (tp_eff + fp_eff) if (tp_eff + fp_eff) > 0 else None
    recall = tp_eff / (tp_eff + fn) if (tp_eff + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None

    return {
        "n": n,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "partial": partial,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
    }


def f1_status(f1_val: float | None, n: int, min_n: int) -> str:
    if n < min_n:
        return "insufficient_data"
    if f1_val is None:
        return "insufficient_data"
    if f1_val >= 0.85:
        return "high"
    if f1_val >= 0.70:
        return "moderate"
    if f1_val >= 0.50:
        return "low"
    return "unreliable"


def behavior_adjustment(status: str) -> str:
    return {
        "high": "proceed_normally",
        "moderate": "increase_cov_threshold",
        "low": "force_review_required",
        "unreliable": "suspend_route_segment",
        "insufficient_data": "collect_more_feedback",
    }.get(status, "proceed_normally")


# ---------------------------------------------------------------------------
# Full report
# ---------------------------------------------------------------------------

def generate_report(records: list[dict]) -> dict:
    # Overall
    all_stats = _f1_from_records(records)
    overall_f1 = all_stats["f1"]

    # By route
    by_route = {}
    for route in ROUTES:
        subset = [r for r in records if r.get("route") == route]
        stats = _f1_from_records(subset)
        status = f1_status(stats["f1"], stats["n"], MIN_SAMPLES["route"])
        by_route[route] = {**stats, "f1_status": status, "adjustment": behavior_adjustment(status)}

    # By clause group
    by_clause = {}
    for cg in CLAUSE_GROUPS:
        subset = [r for r in records if r.get("clause_group", "").startswith(cg)]
        stats = _f1_from_records(subset)
        status = f1_status(stats["f1"], stats["n"], MIN_SAMPLES["clause_group"])
        by_clause[cg] = {**stats, "f1_status": status, "adjustment": behavior_adjustment(status)}

    # By verdict type
    by_verdict = {}
    for vt in VERDICT_TYPES:
        subset = [r for r in records if r.get("verdict_given") == vt]
        stats = _f1_from_records(subset)
        status = f1_status(stats["f1"], stats["n"], MIN_SAMPLES["verdict_type"])
        by_verdict[vt] = {**stats, "f1_status": status}

    # Alerts
    alerts = []
    for route, data in by_route.items():
        if data["f1_status"] in ("low", "unreliable", "moderate"):
            alerts.append({
                "segment": f"route:{route}",
                "f1": data["f1"],
                "f1_status": data["f1_status"],
                "adjustment": data["adjustment"],
            })
    for cg, data in by_clause.items():
        if data["f1_status"] in ("low", "unreliable"):
            alerts.append({
                "segment": f"clause_group:{cg}",
                "f1": data["f1"],
                "f1_status": data["f1_status"],
                "adjustment": data["adjustment"],
            })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_feedback_events": len(records),
        "overall_f1": overall_f1,
        "overall_stats": all_stats,
        "by_route": by_route,
        "by_clause_group": by_clause,
        "by_verdict_type": by_verdict,
        "alerts": alerts,
    }

    # Save to file
    F1_STATS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with F1_STATS_OUT.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


# ---------------------------------------------------------------------------
# Check a specific route's behavior level
# ---------------------------------------------------------------------------

def check_route(route: str) -> dict:
    records = load_feedback()
    subset = [r for r in records if r.get("route") == route]
    stats = _f1_from_records(subset)
    status = f1_status(stats["f1"], stats["n"], MIN_SAMPLES["route"])
    return {
        "route": route,
        **stats,
        "f1_status": status,
        "adjustment": behavior_adjustment(status),
        "instruction_th": _adjustment_instruction_th(status),
    }


def _adjustment_instruction_th(status: str) -> str:
    return {
        "high": "ดำเนินการปกติ — ความน่าเชื่อถือสูง",
        "moderate": "เพิ่มความเข้มข้นของ CoV ขึ้น 1 ระดับ",
        "low": "บังคับ ReviewRequired สำหรับทุก verdict ใน segment นี้ แจ้งผู้ใช้ด้วย",
        "unreliable": "ระงับ segment — คืนค่า ReviewRequired เสมอจนกว่าจะ upskill",
        "insufficient_data": "เก็บ feedback เพิ่มก่อน — ยังไม่มีข้อมูลเพียงพอ",
    }.get(status, "ดำเนินการปกติ")


# ---------------------------------------------------------------------------
# Reset a segment
# ---------------------------------------------------------------------------

def reset_segment(segment: str, note: str) -> dict:
    """Mark all records of a segment as excluded by writing a reset event."""
    F1_RESET_LOG.parent.mkdir(parents=True, exist_ok=True)
    reset_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "segment": segment,
        "note": note,
        "action": "reset",
    }
    with F1_RESET_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reset_record, ensure_ascii=False) + "\n")
    return {
        "status": "reset_logged",
        "segment": segment,
        "note": note,
        "message": "Reset event logged. Recompute F1 report to see updated stats.",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="QMS F1 tracker")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--route", default=None)
    parser.add_argument("--clause-group", default=None, dest="clause_group")
    parser.add_argument("--check-route", default=None, dest="check_route")
    parser.add_argument("--reset-segment", default=None, dest="reset_segment")
    parser.add_argument("--note", default="", help="Required note when resetting a segment")
    args = parser.parse_args(argv[1:])

    if args.reset_segment:
        if not args.note:
            print(json.dumps({"error": "--note is required when resetting a segment"}, ensure_ascii=False))
            return 2
        result = reset_segment(args.reset_segment, args.note)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.check_route:
        result = check_route(args.check_route)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.report:
        records = load_feedback()
        if args.route:
            records = [r for r in records if r.get("route") == args.route]
        if args.clause_group:
            records = [r for r in records if r.get("clause_group", "").startswith(args.clause_group)]
        report = generate_report(records)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
