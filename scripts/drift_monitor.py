#!/usr/bin/env python3
"""
drift_monitor.py — QMS Skill F1 Drift Monitor

ทุกครั้งที่รัน จะ:
  1. โหลด f1_stats.json ปัจจุบัน (สร้างโดย f1_tracker.py)
  2. เปรียบเทียบกับ snapshot ล่าสุดใน assets/stats/f1_snapshots/
  3. คำนวณ drift (delta F1) ต่อ route และ clause_group
  4. บันทึก snapshot ใหม่ + drift_log.jsonl
  5. คืน drift report พร้อม alert ถ้า drift เกิน threshold

Usage:
  python scripts/drift_monitor.py                    # run + report
  python scripts/drift_monitor.py --alert-only       # เฉพาะ drift ที่เกิน threshold
  python scripts/drift_monitor.py --history 5        # แสดง 5 snapshot ล่าสุด
  python scripts/drift_monitor.py --export report.json

Drift thresholds:
  WARN:  F1 ลดลง >= 0.05 (5 points) จาก snapshot ก่อนหน้า
  ALERT: F1 ลดลง >= 0.10 (10 points)
  CRITICAL: F1 ลดลงติดต่อกัน 2 snapshot + >=0.05 ต่อครั้ง
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SKILL_ROOT  = Path(__file__).resolve().parents[1]
F1_STATS    = SKILL_ROOT / "assets" / "stats" / "f1_stats.json"
SNAPSHOTS_DIR = SKILL_ROOT / "assets" / "stats" / "f1_snapshots"
DRIFT_LOG   = SKILL_ROOT / "assets" / "stats" / "drift_log.jsonl"

DRIFT_WARN     = 0.05   # F1 drop ที่ถือว่า warn
DRIFT_ALERT    = 0.10   # F1 drop ที่ถือว่า alert
MAX_SNAPSHOTS  = 30     # เก็บ snapshot ย้อนหลังสูงสุด

ROUTES = [
    "nc_classification", "conformity_evaluation",
    "predictive_risk_scoring", "audit_workflow",
    "iso_clause_advisor", "full_ahp_evaluation",
]
CLAUSE_GROUPS = ["4", "5", "6", "7", "8", "8.4", "8.5", "9", "10"]


# ── Snapshot I/O ──────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_current_stats() -> Optional[dict]:
    if not F1_STATS.exists():
        return None
    try:
        with F1_STATS.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def list_snapshots() -> list[Path]:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(SNAPSHOTS_DIR.glob("f1_snapshot_*.json"))


def load_latest_snapshot() -> Optional[dict]:
    snaps = list_snapshots()
    if not snaps:
        return None
    try:
        with snaps[-1].open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_snapshot(stats: dict) -> Path:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    path = SNAPSHOTS_DIR / f"f1_snapshot_{ts}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump({**stats, "_snapshot_ts": ts}, f, ensure_ascii=False, indent=2)

    # prune เก่าเกิน MAX_SNAPSHOTS
    snaps = list_snapshots()
    for old in snaps[:-MAX_SNAPSHOTS]:
        old.unlink(missing_ok=True)

    return path


def append_drift_log(record: dict) -> None:
    DRIFT_LOG.parent.mkdir(parents=True, exist_ok=True)
    record["ts"] = _ts()
    with DRIFT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── Drift computation ─────────────────────────────────────────────────────────

def _f1_of(stats: dict, segment_type: str, segment_key: str) -> Optional[float]:
    """ดึง F1 จาก stats สำหรับ segment ที่ระบุ"""
    if segment_type == "route":
        return stats.get("by_route", {}).get(segment_key, {}).get("f1")
    elif segment_type == "clause_group":
        return stats.get("by_clause_group", {}).get(segment_key, {}).get("f1")
    elif segment_type == "overall":
        return stats.get("overall_f1")
    return None


def _drift_level(delta: float) -> str:
    if delta <= -DRIFT_ALERT:
        return "ALERT"
    if delta <= -DRIFT_WARN:
        return "WARN"
    if delta >= DRIFT_WARN:
        return "IMPROVING"
    return "STABLE"


def compute_drift(current: dict, previous: dict) -> dict:
    """เปรียบเทียบ current vs previous snapshot คืน drift report"""
    drifts = []

    # Overall
    cur_f1 = _f1_of(current, "overall", "")
    prev_f1 = _f1_of(previous, "overall", "")
    if cur_f1 is not None and prev_f1 is not None:
        delta = cur_f1 - prev_f1
        drifts.append({
            "segment": "overall",
            "current_f1": cur_f1,
            "previous_f1": prev_f1,
            "delta": round(delta, 4),
            "level": _drift_level(delta),
        })

    # By route
    for route in ROUTES:
        cur = _f1_of(current, "route", route)
        prev = _f1_of(previous, "route", route)
        if cur is None or prev is None:
            continue
        delta = cur - prev
        if abs(delta) >= 0.01:  # skip noise < 1%
            drifts.append({
                "segment": f"route:{route}",
                "current_f1": cur,
                "previous_f1": prev,
                "delta": round(delta, 4),
                "level": _drift_level(delta),
            })

    # By clause group
    for cg in CLAUSE_GROUPS:
        cur = _f1_of(current, "clause_group", cg)
        prev = _f1_of(previous, "clause_group", cg)
        if cur is None or prev is None:
            continue
        delta = cur - prev
        if abs(delta) >= 0.01:
            drifts.append({
                "segment": f"clause_group:{cg}",
                "current_f1": cur,
                "previous_f1": prev,
                "delta": round(delta, 4),
                "level": _drift_level(delta),
            })

    alerts = [d for d in drifts if d["level"] in ("ALERT", "WARN")]
    critical = _detect_consecutive_drops(drifts)

    return {
        "snapshot_count": len(list_snapshots()),
        "current_ts": current.get("generated_at", "unknown"),
        "previous_ts": previous.get("generated_at", "unknown"),
        "drifts": drifts,
        "alerts": alerts,
        "critical": critical,
        "summary": {
            "total_segments": len(drifts),
            "improving": sum(1 for d in drifts if d["level"] == "IMPROVING"),
            "stable": sum(1 for d in drifts if d["level"] == "STABLE"),
            "warn": sum(1 for d in drifts if d["level"] == "WARN"),
            "alert": sum(1 for d in drifts if d["level"] == "ALERT"),
            "critical_segments": len(critical),
        },
    }


def _detect_consecutive_drops(drifts: list[dict]) -> list[dict]:
    """ตรวจว่า segment ไหนมี F1 ลดลงต่อเนื่อง (จาก drift log ย้อนหลัง)"""
    critical = []
    snaps = list_snapshots()
    if len(snaps) < 3:
        return critical

    # ดู 2 snapshot ก่อนหน้า
    try:
        with snaps[-2].open(encoding="utf-8") as f:
            prev2 = json.load(f)
        with snaps[-3].open(encoding="utf-8") as f:
            prev3 = json.load(f)
    except (json.JSONDecodeError, OSError, IndexError):
        return critical

    for d in drifts:
        seg = d["segment"]
        if d["level"] not in ("ALERT", "WARN"):
            continue

        # ตรวจว่า segment นี้ drop ใน prev2 vs prev3 ด้วยไหม
        seg_type, seg_key = (seg.split(":", 1) + [""])[:2]
        f1_prev2 = _f1_of(prev2, seg_type, seg_key) if seg_type in ("route", "clause_group") else prev2.get("overall_f1")
        f1_prev3 = _f1_of(prev3, seg_type, seg_key) if seg_type in ("route", "clause_group") else prev3.get("overall_f1")

        if f1_prev2 is not None and f1_prev3 is not None:
            delta_prev = f1_prev2 - f1_prev3
            if delta_prev <= -DRIFT_WARN:
                critical.append({
                    "segment": seg,
                    "drops": [round(delta_prev, 4), d["delta"]],
                    "message": (
                        f"Consecutive F1 drops detected in '{seg}' — "
                        f"drop1={delta_prev:+.3f}, drop2={d['delta']:+.3f}. "
                        "Consider upskill or segment reset."
                    ),
                })

    return critical


# ── History display ───────────────────────────────────────────────────────────

def show_history(n: int) -> list[dict]:
    snaps = list_snapshots()[-n:]
    rows = []
    for snap_path in snaps:
        try:
            with snap_path.open(encoding="utf-8") as f:
                s = json.load(f)
            rows.append({
                "snapshot": snap_path.name,
                "generated_at": s.get("generated_at", "?"),
                "overall_f1": s.get("overall_f1"),
                "total_feedback": s.get("total_feedback_events", 0),
                "alerts": [
                    f"{k}={v.get('f1_status')}"
                    for k, v in s.get("by_route", {}).items()
                    if v.get("f1_status") in ("low", "unreliable")
                ],
            })
        except (json.JSONDecodeError, OSError):
            continue
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def run(alert_only: bool = False, export_path: Optional[str] = None) -> dict:
    current = load_current_stats()
    if not current:
        return {"error": "f1_stats.json not found — run f1_tracker.py --report first"}

    previous = load_latest_snapshot()

    if previous is None:
        # ครั้งแรก — แค่บันทึก snapshot
        snap_path = save_snapshot(current)
        result = {
            "status": "first_snapshot",
            "snapshot_saved": snap_path.name,
            "message": "First snapshot saved. Run again after collecting more feedback to detect drift.",
            "current_f1": current.get("overall_f1"),
        }
        append_drift_log({"event": "first_snapshot", "f1": current.get("overall_f1")})
        return result

    # คำนวณ drift
    drift_report = compute_drift(current, previous)

    # บันทึก snapshot ใหม่เฉพาะเมื่อ feedback เพิ่มขึ้น
    prev_total = previous.get("total_feedback_events", 0)
    cur_total = current.get("total_feedback_events", 0)
    new_snap = None
    if cur_total > prev_total:
        new_snap = save_snapshot(current)
        drift_report["new_snapshot"] = new_snap.name

    # บันทึก drift log เฉพาะ alerts
    if drift_report["alerts"] or drift_report["critical"]:
        append_drift_log({
            "event": "drift_detected",
            "alerts": drift_report["alerts"],
            "critical": drift_report["critical"],
        })

    if export_path:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(drift_report, f, ensure_ascii=False, indent=2)
        drift_report["exported_to"] = export_path

    if alert_only:
        return {
            "alerts": drift_report["alerts"],
            "critical": drift_report["critical"],
            "summary": drift_report["summary"],
        }

    return drift_report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="QMS F1 Drift Monitor")
    parser.add_argument("--alert-only", action="store_true", help="Show only alerts/critical")
    parser.add_argument("--history", type=int, default=0, metavar="N", help="Show last N snapshots")
    parser.add_argument("--export", default=None, metavar="FILE", help="Export report to JSON file")
    args = parser.parse_args(argv[1:])

    if args.history > 0:
        rows = show_history(args.history)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    result = run(alert_only=args.alert_only, export_path=args.export)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Exit code: 0=ok, 1=critical drift, 2=warn drift
    if result.get("critical"):
        return 1
    if result.get("alerts"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
