#!/usr/bin/env python3
"""Build a source-trace payload for human-auditor outputs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = SKILL_ROOT / "assets/manifests/bundled-source-manifest.json"


def _load_manifest() -> dict[str, Any]:
    with MANIFEST.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_trace(source_id: str, *, page: str | None = None, clause: str | None = None, chunk_id: str | None = None, retrieval_mode: str = "bundled_only", evidence_role: str = "controlled_source") -> dict[str, Any]:
    manifest = _load_manifest()
    source = next((s for s in manifest.get("sources", []) if s.get("source_id") == source_id), None)
    if not source:
        return {"status":"ReferenceGap", "reason":"unknown_source_id", "source_id":source_id}
    return {
        "status":"trace_built",
        "retrieval_mode": retrieval_mode,
        "evidence_role": evidence_role,
        "source_id": source_id,
        "source_title": source.get("title"),
        "source_category": source.get("source_category"),
        "controlled_location": source.get("controlled_location"),
        "checksum_sha256": source.get("checksum_sha256"),
        "page": page,
        "clause": clause,
        "chunk_id": chunk_id,
        "source_boundary": "controlled_sources_only",
        "external_sources_used": False,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-id", required=True)
    p.add_argument("--page")
    p.add_argument("--clause")
    p.add_argument("--chunk-id")
    p.add_argument("--retrieval-mode", default="bundled_only")
    p.add_argument("--evidence-role", default="controlled_source")
    args = p.parse_args(argv[1:])
    result = build_trace(args.source_id, page=args.page, clause=args.clause, chunk_id=args.chunk_id, retrieval_mode=args.retrieval_mode, evidence_role=args.evidence_role)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "trace_built" else 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
