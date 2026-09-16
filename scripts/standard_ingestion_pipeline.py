#!/usr/bin/env python3
"""Prepare a new controlled standard/source for bundling.

This script is intentionally conservative. It can copy a user-supplied file into
`assets/standards/custom/`, register metadata in the manifest, and leave indexing
to `standard_index_builder.py`. It does not search the web or verify latest status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SKILL_ROOT / "assets/manifests/bundled-source-manifest.json"
FORBIDDEN_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "drive://", "sharepoint://", "slack://")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:80] or "controlled-source"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()


def _load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(data: dict[str, Any]) -> None:
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def register_source(args: argparse.Namespace) -> dict[str, Any]:
    raw = args.file
    if raw.lower().startswith(FORBIDDEN_PREFIXES):
        return {"status":"blocked_pending_controlled_source", "reason":"external_location_forbidden"}
    src = Path(raw).resolve()
    if not src.exists() or not src.is_file():
        return {"status":"error", "reason":"file_not_found", "file": raw}
    manifest = _load_manifest()
    sid = args.source_id or _slug(args.title)
    if any(s.get("source_id") == sid for s in manifest.get("sources", [])):
        return {"status":"error", "reason":"duplicate_source_id", "source_id": sid}
    dest_dir = SKILL_ROOT / "assets/standards/custom"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{sid}{src.suffix.lower()}"
    shutil.copy2(src, dest)
    rel = str(dest.relative_to(SKILL_ROOT))
    entry = {
        "source_id": sid,
        "title": args.title,
        "source_category": args.source_category,
        "status": args.status,
        "language": args.language,
        "controlled_location": rel,
        "checksum_sha256": _sha256(dest),
        "knowledge_roles": [x.strip() for x in args.knowledge_roles.split(",") if x.strip()],
        "allowed_use": [x.strip() for x in args.allowed_use.split(",") if x.strip()],
        "allowed_outputs": ["short summary", "thai explanation", "audit impact summary", "source trace"],
        "prohibited_outputs": ["long verbatim quotation", "full document reproduction", "uncited interpretation", "web comparison"],
        "external_access_allowed": False,
        "requires_human_auditor_contract": True,
    }
    manifest.setdefault("sources", []).append(entry)
    _save_manifest(manifest)
    return {"status":"registered_controlled_source", "source": entry, "next_step":"run scripts/source_manifest_validator.py then scripts/standard_index_builder.py"}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--source-id")
    p.add_argument("--source-category", default="standard")
    p.add_argument("--status", default="controlled_upload")
    p.add_argument("--language", default="en")
    p.add_argument("--knowledge-roles", default="definition_lookup,clause_interpretation,audit_evaluation")
    p.add_argument("--allowed-use", default="definition lookup,clause interpretation,audit evaluation,certification impact")
    args = p.parse_args(argv[1:])
    result = register_source(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "registered_controlled_source" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
