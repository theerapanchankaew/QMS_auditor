#!/usr/bin/env python3
"""Create a structured evidence pack for QMS clause assessment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from retrieval_engine import build_evidence_pack, detect_clause, load_json, simple_yaml_map, validate_pack


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, help="Path to clause_index JSON")
    parser.add_argument("--related", required=True, help="Path to related_clause_map.yaml")
    parser.add_argument("--clause", help="Requested clause, e.g. 4.1")
    parser.add_argument("--query", default="", help="User query")
    parser.add_argument("--no-related", action="store_true", help="Do not include related requirement clauses")
    parser.add_argument("--no-informative", action="store_true", help="Do not include Annex/informative clauses")
    parser.add_argument("--out", help="Output JSON path")
    args = parser.parse_args()

    index = load_json(args.index)
    related = simple_yaml_map(args.related)
    clause = args.clause or detect_clause(args.query)
    if not clause:
        raise SystemExit("No clause provided and no clause detected in query.")

    pack = build_evidence_pack(
        index=index,
        related_map=related,
        requested_clause=clause,
        query=args.query,
        include_related=not args.no_related,
        include_informative=not args.no_informative,
    )
    pack["validation_result"] = validate_pack(pack)

    text = json.dumps(pack, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
