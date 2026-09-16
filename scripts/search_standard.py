#!/usr/bin/env python3
"""Search the bundled ISO/FDIS 9001:2026 PDF and return compact evidence snippets.

Usage:
  python scripts/search_standard.py "quality culture" --max 5
  python scripts/search_standard.py "planning of changes" --context 250
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from controlled_source_guardrail import GuardrailDialogRequired, assert_path_inside_skill, print_guardrail_and_exit

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyMuPDF/fitz is required: {exc}")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "assets" / "standards" / "ISO_FDIS_9001_2026_en.pdf"

HEADER_RE = re.compile(r"ISO/FDIS 9001:2026\(en\)|© ISO 2025.*?reserved|^\s*\d+\s*$", re.I | re.M)
SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = HEADER_RE.sub(" ", text)
    text = text.replace("\u00ad", "")
    return SPACE_RE.sub(" ", text).strip()


def terms(query: str) -> list[str]:
    words = re.findall(r"[\w\-\.]+", query.lower())
    return [w for w in words if len(w) > 1]


def score_text(text: str, query_terms: Iterable[str], phrase: str) -> int:
    low = text.lower()
    unique_hits = sum(1 for term in query_terms if term in low)
    score = unique_hits * 5
    if query_terms and unique_hits == len(query_terms):
        score += 30
    if phrase and phrase.lower() in low:
        score += 100
    for term in query_terms:
        score += min(low.count(term), 5)
    return score


def make_snippet(text: str, query_terms: list[str], phrase: str, context: int) -> str:
    low = text.lower()
    idx = low.find(phrase.lower()) if phrase else -1
    if idx < 0:
        hits = [low.find(t) for t in query_terms if low.find(t) >= 0]
        idx = min(hits) if hits else 0
    start = max(0, idx - context)
    end = min(len(text), idx + max(len(phrase), 1) + context)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the bundled ISO/FDIS 9001:2026 PDF.")
    parser.add_argument("query", help="Search phrase or keywords")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Path to standard PDF")
    parser.add_argument("--max", type=int, default=8, help="Maximum number of results")
    parser.add_argument("--context", type=int, default=180, help="Characters around match")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    parser.add_argument("--allow-external-pdf", action="store_true", help="Allow a PDF outside the skill bundle only after explicit user approval")
    parser.add_argument("--approval-text", default="", help="Required explicit user confirmation text for external PDF access")
    args = parser.parse_args()

    try:
        approval = {"external_access_approval": {"allowed": bool(args.allow_external_pdf), "approval_text": args.approval_text}}
        pdf_path = assert_path_inside_skill(args.pdf, purpose="standard search PDF", approval=approval)
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    q_terms = terms(args.query)
    if not q_terms:
        raise SystemExit("Query must contain at least one searchable term")

    results = []
    doc = fitz.open(pdf_path)
    for page_index, page in enumerate(doc):
        text = clean_text(page.get_text("text"))
        if not text:
            continue
        score = score_text(text, q_terms, args.query)
        if score <= 0:
            continue
        results.append({
            "page": page_index + 1,
            "score": score,
            "snippet": make_snippet(text, q_terms, args.query, args.context),
        })

    results.sort(key=lambda r: (-r["score"], r["page"]))
    results = results[: max(args.max, 1)]

    payload = {
        "source": str(pdf_path.relative_to(ROOT) if pdf_path.is_relative_to(ROOT) else pdf_path),
        "query": args.query,
        "results": results,
        "note": "Use snippets for locating clauses and verifying short wording only; do not reproduce long passages from the standard.",
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Source: {payload['source']}")
        print(f"Query: {args.query}")
        print(f"Results: {len(results)}")
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] page {r['page']} score {r['score']}")
            print(r["snippet"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
