#!/usr/bin/env python3
"""Resolve QMS/ISO requests only against bundled references and assets.

This script is intentionally offline and fail-closed. It never calls web search,
network APIs, connectors, or model memory. It searches only files inside the
skill bundle under references/ and assets/ (including bundled standard PDFs).

Usage:
  python scripts/local_source_resolver.py --query "dispute recovery provider definition"
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from controlled_source_guardrail import (
    GuardrailDialogRequired,
    SKILL_ROOT,
    assert_no_external_intent_text,
    print_guardrail_and_exit,
)
from human_auditor_contract import build_contract

ALLOWED_DIRS = [SKILL_ROOT / "references", SKILL_ROOT / "assets"]
TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}
PDF_EXTENSIONS = {".pdf"}
EXCLUDED_SOURCE_NAME_PARTS = {"17-knowledge-boundary-enforcement", "closed-source-policy", "refusal-and-escalation-rules"}
STOPWORDS = {"definition", "define", "meaning", "term", "terms", "คือ", "นิยาม", "คำจำกัดความ", "ความหมาย"}

# Closed-source synonym map for common user wording errors. This does not add
# outside knowledge; it only improves retrieval against bundled ISO sources.
QUERY_SYNONYMS = {
    "dispute recovery provider": "dispute resolution process provider",
    "recovery provider": "resolution process provider",
    "drp provider": "DRP-provider dispute resolution process provider",
}


def _normalize_query(text: str) -> str:
    normalized = text or ""
    low = normalized.lower()
    for wrong, preferred in QUERY_SYNONYMS.items():
        if wrong in low:
            normalized = normalized + " " + preferred
    return normalized


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9_:/.-]*|[\u0E00-\u0E7F]+", text or "") if len(t) > 1]


def _iter_allowed_files() -> list[Path]:
    files: list[Path] = []
    for root in ALLOWED_DIRS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS | PDF_EXTENSIONS:
                continue
            rel = str(path.relative_to(SKILL_ROOT)).lower()
            if any(part in rel for part in EXCLUDED_SOURCE_NAME_PARTS):
                continue
            files.append(path)
    return sorted(files)


@lru_cache(maxsize=16)
def _pdf_pages(path_str: str) -> tuple[str, ...]:
    """Extract text page-by-page from bundled PDFs only.

    Fail closed: extraction failures simply produce no searchable content for the
    file; they never trigger web fallback or connector lookup.
    """
    path = Path(path_str)
    if not str(path.resolve()).startswith(str(SKILL_ROOT.resolve())):
        return tuple()
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return tuple(pages)
    except Exception:
        return tuple()


def _iter_search_units(path: Path) -> list[dict[str, Any]]:
    rel_path = str(path.relative_to(SKILL_ROOT))
    if path.suffix.lower() in TEXT_EXTENSIONS:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []
        return [
            {"path": rel_path, "line": idx, "page": None, "text": line.strip()}
            for idx, line in enumerate(text.splitlines(), start=1)
            if line.strip()
        ]
    if path.suffix.lower() in PDF_EXTENSIONS:
        units: list[dict[str, Any]] = []
        for pageno, text in enumerate(_pdf_pages(str(path)), start=1):
            # Split pages into manageable pseudo-lines/sentences while keeping page trace.
            chunks = re.split(r"(?<=[.;:])\s+|\n+", text)
            for idx, chunk in enumerate(chunks, start=1):
                clean = re.sub(r"\s+", " ", chunk).strip()
                if clean:
                    units.append({"path": rel_path, "line": idx, "page": pageno, "text": clean})
        return units
    return []


def search_local_sources(query: str, *, max_results: int = 8) -> dict[str, Any]:
    assert_no_external_intent_text(query, context="local controlled-source query")
    normalized_query = _normalize_query(query)
    qtokens = {t for t in _tokens(normalized_query) if t not in STOPWORDS}
    if not qtokens:
        return {"status": "ReferenceGap", "results": [], "message": "Empty or unsupported query."}

    results: list[dict[str, Any]] = []
    required_overlap = 1 if len(qtokens) <= 2 else max(2, math.ceil(len(qtokens) * 0.45))
    normalized_lower = normalized_query.lower()

    for path in _iter_allowed_files():
        for unit in _iter_search_units(path):
            text = unit["text"]
            line_tokens = set(_tokens(text))
            overlap = qtokens & line_tokens
            phrase_hit = query.lower() in text.lower() or normalized_lower in text.lower()
            # Also accept exact preferred phrase hits from synonym-expanded queries.
            synonym_hit = any(preferred.lower() in text.lower() for preferred in QUERY_SYNONYMS.values() if preferred.lower() in normalized_lower)
            if phrase_hit or synonym_hit or len(overlap) >= required_overlap:
                rel_path = unit["path"]
                source_bonus = 5 if "references/standard/" in rel_path else 0
                source_bonus += 4 if "assets/standards/" in rel_path else 0
                source_bonus += 3 if "definition-index" in rel_path else 0
                source_bonus += 2 if "9000" in rel_path else 0
                score = (12 if phrase_hit else 0) + (10 if synonym_hit else 0) + len(overlap) + source_bonus
                result = {
                    "path": rel_path,
                    "line": unit["line"],
                    "score": score,
                    "excerpt": text[:500],
                }
                if unit.get("page") is not None:
                    result["page"] = unit["page"]
                results.append(result)
    results.sort(key=lambda r: (-r["score"], r["path"], r.get("page") or 0, r["line"]))
    results = results[:max_results]
    if not results:
        return {
            "guardrail": "closed_source_local_resolver",
            "status": "ReferenceGap",
            "human_auditor_contract": build_contract(objective=query, route="definition_or_source_lookup", status="ReferenceGap"),
            "results": [],
            "message_th": (
                "ไม่พบคำ/นิยาม/หลักฐานนี้ใน references หรือ assets ที่อยู่ภายใน skill bundle. "
                "ห้ามค้นเว็บหรือใช้แหล่งภายนอกเพื่อเติมคำตอบ ให้ผู้ใช้อัปโหลดเอกสารทางการหรือหลักฐานที่ต้องการให้ใช้เป็น controlled source ก่อน."
            ),
            "message_en": (
                "The term/evidence was not found in bundled references or assets. Do not search the web or use external sources to fill the gap. Request an uploaded controlled source."
            ),
            "query": query,
            "normalized_query": normalized_query,
            "searched_roots": [str(p.relative_to(SKILL_ROOT)) for p in ALLOWED_DIRS if p.exists()],
        }
    return {
        "guardrail": "closed_source_local_resolver",
        "status": "found_in_controlled_sources",
        "human_auditor_contract": build_contract(objective=query, route="definition_or_source_lookup", status="found_in_controlled_sources"),
        "query": query,
        "normalized_query": normalized_query,
        "results": results,
        "searched_roots": [str(p.relative_to(SKILL_ROOT)) for p in ALLOWED_DIRS if p.exists()],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--max-results", type=int, default=8)
    args = parser.parse_args(argv[1:])
    try:
        result = search_local_sources(args.query, max_results=args.max_results)
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "found_in_controlled_sources" else 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
