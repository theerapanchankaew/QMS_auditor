#!/usr/bin/env python3
"""Look up ISO 9001 structural AHP score and treatment band."""
import csv
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "references" / "data" / "iso9001_structural_ahp_model_scored.csv"


def band(score):
    if score >= 3.0:
        return "high_structural_importance", "require stronger evidence, deeper sampling, and lower tolerance for gaps"
    if score >= 2.0:
        return "medium_high_importance", "require clear evidence linkage and explicit risk consideration"
    if score >= 1.0:
        return "standard_importance", "apply normal verification and evidence sufficiency rules"
    return "supporting_local_importance", "avoid over-escalation unless other risk triggers exist"


def main():
    if len(sys.argv) != 2:
        print("Usage: score_clause_priority.py <clause_id>", file=sys.stderr)
        return 2
    clause = sys.argv[1].strip()
    matches = []
    with DATA.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            node = (row.get("Node") or "").strip()
            score_raw = (row.get("Score (0-4)") or "").strip()
            if node == clause or node.startswith(clause + ".") or clause.startswith(node + "."):
                try:
                    score = float(score_raw)
                except ValueError:
                    continue
                b, treatment = band(score)
                matches.append({
                    "node": node,
                    "node_title": row.get("Node Title", ""),
                    "id": row.get("ID", ""),
                    "role": row.get("Role", ""),
                    "score": score,
                    "band": b,
                    "treatment": treatment,
                })
    if not matches:
        print(json.dumps({"clause_id": clause, "found": False}, ensure_ascii=False))
        return 1
    avg = sum(m["score"] for m in matches) / len(matches)
    b, treatment = band(avg)
    print(json.dumps({
        "clause_id": clause,
        "found": True,
        "average_score": round(avg, 3),
        "band": b,
        "treatment": treatment,
        "matches": matches[:20],
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
