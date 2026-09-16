#!/usr/bin/env python3
"""Evaluate clause retrieval on a JSONL test set.

Each line should contain:
{"query":"...", "expected_primary":["4.1"], "must_include_related":["6.1"], "must_not_primary":["A.5.2"]}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from retrieval_engine import build_evidence_pack, detect_clause, load_json, simple_yaml_map


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--related", required=True)
    parser.add_argument("--tests", required=True)
    args = parser.parse_args()

    index = load_json(args.index)
    related = simple_yaml_map(args.related)
    rows = [json.loads(line) for line in Path(args.tests).read_text(encoding="utf-8").splitlines() if line.strip()]

    total = len(rows)
    primary_ok = 0
    related_ok = 0
    forbidden_ok = 0
    details = []

    for row in rows:
        query = row["query"]
        clause = row.get("requested_clause") or detect_clause(query)
        pack = build_evidence_pack(index, related, clause, query=query) if clause else {"primary_evidence": [], "related_evidence": []}
        primary_ids = {x["clause_id"] for x in pack.get("primary_evidence", [])}
        related_ids = {x["clause_id"] for x in pack.get("related_evidence", [])}
        expected_primary = set(row.get("expected_primary", []))
        must_related = set(row.get("must_include_related", []))
        must_not_primary = set(row.get("must_not_primary", []))

        p_ok = expected_primary.issubset(primary_ids)
        r_ok = must_related.issubset(related_ids | primary_ids)
        f_ok = not (must_not_primary & primary_ids)
        primary_ok += int(p_ok)
        related_ok += int(r_ok)
        forbidden_ok += int(f_ok)
        details.append({
            "query": query,
            "primary_ids": sorted(primary_ids),
            "related_ids": sorted(related_ids),
            "primary_ok": p_ok,
            "related_ok": r_ok,
            "forbidden_ok": f_ok,
        })

    result = {
        "total": total,
        "primary_clause_accuracy": round(primary_ok / total, 4) if total else 0,
        "related_recall": round(related_ok / total, 4) if total else 0,
        "forbidden_primary_control": round(forbidden_ok / total, 4) if total else 0,
        "details": details,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
