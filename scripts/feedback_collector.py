#!/usr/bin/env python3
"""Feedback collector for QMS skill.

Appends structured feedback events to assets/stats/feedback_log.jsonl.
Returns cumulative F1 stats for the affected route and clause group.

Usage:
  python scripts/feedback_collector.py \
    --session-id abc123 \
    --route nc_classification \
    --clause-group 8.4 \
    --verdict Major \
    --feedback-type wrong \
    --correction "Should be Minor — only one instance" \
    --confidence high \
    --evidence-count 3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_LOG = SKILL_ROOT / "assets" / "stats" / "feedback_log.jsonl"

# ---------------------------------------------------------------------------
# F1 label mapping
# ---------------------------------------------------------------------------

POSITIVE_VERDICTS = {"Noncomplied", "Major", "Minor", "OBS", "OFI"}
NEGATIVE_VERDICTS = {"Complied", "InsufficientEvidence", "ReferenceGap", "ReviewRequired"}


def compute_f1_label(verdict: str, feedback_type: str) -> str:
    """Map (verdict, feedback_type) → F1 label."""
    is_positive = verdict in POSITIVE_VERDICTS
    if feedback_type == "skip":
        return "skip"
    if feedback_type == "correct":
        return "TP" if is_positive else "TN"
    if feedback_type == "wrong":
        return "FP" if is_positive else "FN"
    if feedback_type == "partial":
        return "partial"  # counted as 0.5 TP + 0.5 FP in tracker
    return "skip"


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def ensure_log_exists() -> None:
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_LOG.exists():
        FEEDBACK_LOG.touch()


def append_feedback(record: dict) -> None:
    ensure_log_exists()
    with FEEDBACK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_all_feedback() -> list[dict]:
    ensure_log_exists()
    records = []
    with FEEDBACK_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


# ---------------------------------------------------------------------------
# Cumulative stats (lightweight — no external deps)
# ---------------------------------------------------------------------------

def compute_cumulative_stats(route: str | None = None, clause_group: str | None = None) -> dict:
    records = load_all_feedback()
    if route:
        records = [r for r in records if r.get("route") == route]
    if clause_group:
        records = [r for r in records if r.get("clause_group") == clause_group]

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

    precision = tp_eff / (tp_eff + fp_eff) if (tp_eff + fp_eff) > 0 else None
    recall = tp_eff / (tp_eff + fn) if (tp_eff + fn) > 0 else None
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None

    n = tp + fp + fn + tn + partial

    return {
        "route_filter": route,
        "clause_filter": clause_group,
        "n": n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "partial": partial,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
        "f1_status": (
            "insufficient_data" if n < 5
            else "high" if (f1 or 0) >= 0.85
            else "moderate" if (f1 or 0) >= 0.70
            else "low" if (f1 or 0) >= 0.50
            else "unreliable"
        ),
    }


# ---------------------------------------------------------------------------
# User feedback dialog parser (helper for the assistant)
# ---------------------------------------------------------------------------

FEEDBACK_TYPE_MAP = {
    # Thai
    "ถูก": "correct",
    "ถูกต้อง": "correct",
    "correct": "correct",
    "ผิด": "wrong",
    "ไม่ถูก": "wrong",
    "ไม่ถูกต้อง": "wrong",
    "wrong": "wrong",
    "บางส่วน": "partial",
    "partial": "partial",
    "ข้าม": "skip",
    "skip": "skip",
}


def parse_user_feedback(raw_response: str) -> str | None:
    """Convert raw user text to a feedback_type key, or return None if unparseable."""
    key = raw_response.strip().lower()
    return FEEDBACK_TYPE_MAP.get(key)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="QMS feedback collector")
    parser.add_argument("--session-id", default="", dest="session_id")
    parser.add_argument("--route", required=True)
    parser.add_argument("--clause-group", default="", dest="clause_group")
    parser.add_argument("--verdict", required=True)
    parser.add_argument("--feedback-type", required=True, dest="feedback_type",
                        choices=["correct", "wrong", "partial", "skip"])
    parser.add_argument("--correction", default=None)
    parser.add_argument("--confidence", default="medium",
                        choices=["high", "medium", "low"])
    parser.add_argument("--evidence-count", default=0, type=int, dest="evidence_count")
    parser.add_argument("--notes", default="")
    args = parser.parse_args(argv[1:])

    session_id = args.session_id or hashlib.md5(
        datetime.now(timezone.utc).isoformat().encode()
    ).hexdigest()[:8]

    f1_label = compute_f1_label(args.verdict, args.feedback_type)

    record = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": args.route,
        "clause_group": args.clause_group,
        "verdict_given": args.verdict,
        "feedback_type": args.feedback_type,
        "correction": args.correction,
        "confidence_given": args.confidence,
        "evidence_count": args.evidence_count,
        "f1_label": f1_label,
        "notes": args.notes,
    }

    append_feedback(record)

    stats = compute_cumulative_stats(
        route=args.route,
        clause_group=args.clause_group or None,
    )

    output = {
        "status": "recorded",
        "record": record,
        "cumulative_stats": stats,
        "message_th": (
            "ขอบคุณครับ — บันทึกการประเมินแล้ว" if args.feedback_type != "skip"
            else "ข้ามการให้คะแนนแล้วครับ"
        ),
    }

    if args.feedback_type in ("wrong", "partial"):
        output["followup_th"] = (
            "ต้องการให้ผมทบทวนและให้คำตอบใหม่โดยอิงจากการแก้ไขนี้ไหมครับ?"
        )

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
