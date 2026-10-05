#!/usr/bin/env python3
"""Build a simple local JSONL index from approved manifest sources.

This creates a local, offline index for `local_rag_adapter.py`. It never calls
network services and never reads files outside the skill root.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SKILL_ROOT / "assets/manifests/bundled-source-manifest.json"
DEFAULT_OUT = SKILL_ROOT / "assets/rag_indexes/bundled-qms-local-index.jsonl"
TEXT_EXTS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}
PDF_EXTS = {".pdf"}


def _load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _inside_skill(rel: str) -> Path:
    p = (SKILL_ROOT / rel).resolve()
    if not str(p).startswith(str(SKILL_ROOT.resolve())):
        raise ValueError(f"path escapes skill root: {rel}")
    return p


def _chunk_text(text: str, max_chars: int = 900) -> list[str]:
    parts = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n+|(?<=[.;:])\s+", text or "")]
    chunks: list[str] = []
    buf = ""
    for part in parts:
        if not part:
            continue
        if len(buf) + len(part) + 1 > max_chars and buf:
            chunks.append(buf)
            buf = part
        else:
            buf = (buf + " " + part).strip()
    if buf:
        chunks.append(buf)
    return chunks


def _pdf_pages(path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return [(page.extract_text() or "") for page in reader.pages]
    except Exception:
        return []


def build_index(output: Path = DEFAULT_OUT) -> dict[str, Any]:
    manifest = _load_manifest()
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as out:
        for src in manifest.get("sources", []):
            sid = src.get("source_id")
            loc = src.get("controlled_location")
            if not sid or not loc:
                continue
            p = _inside_skill(loc)
            files = [p] if p.is_file() else [x for x in p.rglob("*") if x.is_file()]
            for file in files:
                rel = file.relative_to(SKILL_ROOT).as_posix()  # posix separators: index is portable across OSes
                if file.suffix.lower() in TEXT_EXTS:
                    try:
                        text = file.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    for i, chunk in enumerate(_chunk_text(text), start=1):
                        out.write(json.dumps({
                            "chunk_id": f"{sid}:{rel}:{i}",
                            "source_id": sid,
                            "source_title": src.get("title"),
                            "controlled_location": rel,
                            "chunk_index": i,
                            "text": chunk,
                        }, ensure_ascii=False) + "\n")
                        count += 1
                elif file.suffix.lower() in PDF_EXTS:
                    for page_no, page_text in enumerate(_pdf_pages(file), start=1):
                        for i, chunk in enumerate(_chunk_text(page_text), start=1):
                            out.write(json.dumps({
                                "chunk_id": f"{sid}:{rel}:p{page_no}:{i}",
                                "source_id": sid,
                                "source_title": src.get("title"),
                                "controlled_location": rel,
                                "page": page_no,
                                "chunk_index": i,
                                "text": chunk,
                            }, ensure_ascii=False) + "\n")
                            count += 1
    return {"status":"built", "output": output.relative_to(SKILL_ROOT).as_posix(), "chunk_count": count, "external_sources_used": False}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(DEFAULT_OUT.relative_to(SKILL_ROOT)))
    args = p.parse_args(argv[1:])
    out = _inside_skill(args.output)
    result = build_index(out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
