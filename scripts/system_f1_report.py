#!/usr/bin/env python3
"""
system_f1_report.py — QMS Skill System-Level F1 Report Generator

รวม F1 snapshots ทั้งหมดเป็น timeseries และสร้าง markdown report
ใช้สำหรับ quarterly review, upskill decision, release gate documentation

Usage:
  python scripts/system_f1_report.py --output system_f1_report.md
  python scripts/system_f1_report.py --input f1_timeseries.jsonl --output report.md
  python scripts/system_f1_report.py --last 10   # ใช้ 10 snapshot ล่าสุด
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT    = Path(__file__).resolve().parents[1]
SNAPSHOTS_DIR = SKILL_ROOT / "assets" / "stats" / "f1_snapshots"
DRIFT_LOG     = SKILL_ROOT / "assets" / "stats" / "drift_log.jsonl"
DEFAULT_OUT   = SKILL_ROOT / "assets" / "stats" / "system_f1_report.md"

ROUTES = [
    "nc_classification", "conformity_evaluation",
    "predictive_risk_scoring", "audit_workflow",
    "iso_clause_advisor", "full_ahp_evaluation",
]


# ── Snapshot loading ──────────────────────────────────────────────────────────

def load_snapshots(last: int = 0, jsonl_path: str | None = None) -> list[dict]:
    if jsonl_path:
        p = Path(jsonl_path)
        if not p.exists():
            return []
        records = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return records

    snaps = sorted(SNAPSHOTS_DIR.glob("f1_snapshot_*.json"))
    if last > 0:
        snaps = snaps[-last:]
    records = []
    for sp in snaps:
        try:
            with sp.open(encoding="utf-8") as f:
                records.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return records


def load_drift_events(last: int = 20) -> list[dict]:
    if not DRIFT_LOG.exists():
        return []
    events = []
    for line in DRIFT_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                e = json.loads(line)
                if e.get("event") == "drift_detected":
                    events.append(e)
            except json.JSONDecodeError:
                pass
    return events[-last:]


# ── Report generation ─────────────────────────────────────────────────────────

def _trend_arrow(values: list[float | None]) -> str:
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return "—"
    delta = clean[-1] - clean[0]
    if delta > 0.05:
        return "↑"
    if delta < -0.05:
        return "↓"
    return "→"


def generate_report(snapshots: list[dict], drift_events: list[dict]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n_snaps = len(snapshots)

    lines = [
        f"# QMS Auditor — System F1 Report",
        f"Generated: {ts}  |  Snapshots: {n_snaps}",
        "",
        "## Overall F1 Trend",
        "",
        "| Snapshot | Date | Overall F1 | Feedback Events |",
        "| -------- | ---- | ---------- | --------------- |",
    ]

    for i, snap in enumerate(snapshots, 1):
        date = snap.get("generated_at", snap.get("_snapshot_ts", "?"))[:10]
        f1 = snap.get("overall_f1")
        f1_str = f"{f1:.4f}" if f1 is not None else "—"
        n = snap.get("total_feedback_events", 0)
        lines.append(f"| {i} | {date} | {f1_str} | {n} |")

    # Trend indicator
    overall_f1s = [s.get("overall_f1") for s in snapshots]
    lines.append("")
    lines.append(f"**Trend**: {_trend_arrow(overall_f1s)}")
    if overall_f1s and overall_f1s[-1] is not None:
        lines.append(f"**Latest F1**: {overall_f1s[-1]:.4f}")

    # By route — latest snapshot
    if snapshots:
        latest = snapshots[-1]
        lines += [
            "",
            "## Route-Level F1 (Latest Snapshot)",
            "",
            "| Route | F1 | Status | Adjustment |",
            "| ----- | -- | ------ | ---------- |",
        ]
        for route in ROUTES:
            rd = latest.get("by_route", {}).get(route, {})
            f1 = rd.get("f1")
            f1_str = f"{f1:.4f}" if f1 is not None else "—"
            status = rd.get("f1_status", "—")
            adj = rd.get("adjustment", "—")
            lines.append(f"| {route} | {f1_str} | {status} | {adj} |")

    # Drift events
    if drift_events:
        lines += [
            "",
            "## Recent Drift Events",
            "",
        ]
        for ev in drift_events[-5:]:
            ts_ev = ev.get("ts", "?")
            alerts = ev.get("alerts", [])
            critical = ev.get("critical", [])
            lines.append(f"**{ts_ev}**")
            for a in alerts:
                lines.append(f"- [{a.get('level')}] {a.get('segment')} Δ={a.get('delta'):+.3f}")
            for c in critical:
                lines.append(f"- [CRITICAL] {c.get('message','')[:100]}")
            lines.append("")
    else:
        lines += ["", "## Drift Events", "", "_No drift events recorded yet._", ""]

    # Upskill recommendation
    lines += ["", "## Upskill Recommendation", ""]
    if snapshots:
        latest = snapshots[-1]
        suspended = [
            route for route in ROUTES
            if latest.get("by_route", {}).get(route, {}).get("f1_status") in ("unreliable",)
        ]
        low_routes = [
            route for route in ROUTES
            if latest.get("by_route", {}).get(route, {}).get("f1_status") in ("low",)
        ]
        if suspended:
            lines.append(f"⛔ **Suspend** routes: {', '.join(suspended)} — upskill required before re-enabling")
        if low_routes:
            lines.append(f"⚠️ **Force ReviewRequired** for: {', '.join(low_routes)}")
        if not suspended and not low_routes:
            lines.append("✅ All routes within acceptable range — no upskill required")

    lines += [
        "",
        "---",
        f"_Generated by system_f1_report.py | QMS Auditor v5.6.1_",
    ]

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="QMS System F1 Report")
    parser.add_argument("--input", default=None, help="Path to f1_timeseries.jsonl (optional)")
    parser.add_argument("--output", default=str(DEFAULT_OUT), help="Output markdown file")
    parser.add_argument("--last", type=int, default=0, help="Use last N snapshots only")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of file")
    args = parser.parse_args(argv[1:])

    snapshots = load_snapshots(last=args.last, jsonl_path=args.input)
    if not snapshots:
        print("No snapshots found. Run drift_monitor.py first to create snapshots.", file=sys.stderr)
        return 1

    drift_events = load_drift_events()
    report = generate_report(snapshots, drift_events)

    if args.stdout:
        print(report)
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"Report written to: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
