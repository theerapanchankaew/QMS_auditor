#!/usr/bin/env python3
"""Extract a clause from the bundled ISO/FDIS 9001:2026 PDF.

The extractor uses heading patterns in the PDF text layer and returns the matched clause
until the next same-or-higher level clause heading. It is intended for verification and
short audit criteria extraction, not long reproduction.

Usage:
  python scripts/extract_clause.py 6.3
  python scripts/extract_clause.py 9.2 --json
  python scripts/extract_clause.py A.6.1.2 --include-annex
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from controlled_source_guardrail import GuardrailDialogRequired, assert_path_inside_skill, print_guardrail_and_exit

try:
    import fitz
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyMuPDF/fitz is required: {exc}")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "assets" / "standards" / "ISO_FDIS_9001_2026_en.pdf"
HEADER_RE = re.compile(r"ISO/FDIS 9001:2026\(en\)|© ISO 2025.*?reserved|^\s*\d+\s*$", re.I | re.M)
SPACE_RE = re.compile(r"[ \t]+")

# Match clause headings such as "4.1 Understanding...", "7.5.1 General", "10.2.2 Documented...", "A.6.1.2 Risk-based thinking".
HEADING_RE = re.compile(
    r"^(?P<num>(?:\d{1,2}(?:\.\d+){0,3}|A\.\d+(?:\.\d+){0,3}|Annex A|Bibliography))(?P<title>\s+[^\n]{0,140})?$",
    re.M,
)

@dataclass
class Heading:
    num: str
    title: str
    start: int
    page: int
    level: int


def normalize_lines(text: str) -> str:
    text = text.replace("\u00ad", "")
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if HEADER_RE.search(line):
            continue
        lines.append(SPACE_RE.sub(" ", line))
    return "\n".join(lines)


def clause_level(num: str) -> int:
    if num in {"Annex A", "Bibliography"}:
        return 1
    if num.startswith("A."):
        return num.count(".")
    return num.count(".") + 1


def build_text(pdf_path: Path, include_annex: bool) -> tuple[str, list[int]]:
    doc = fitz.open(pdf_path)
    all_text = []
    page_offsets = []
    offset = 0
    for page_index, page in enumerate(doc):
        page_text = normalize_lines(page.get_text("text"))
        if not include_annex and page_index + 1 >= 38:  # Annex A starts on PDF page 38 in this draft
            break
        page_offsets.append(offset)
        all_text.append(page_text)
        offset += len(page_text) + 2
    return "\n\n".join(all_text), page_offsets


def page_for_offset(offset: int, page_offsets: list[int]) -> int:
    page = 1
    for i, po in enumerate(page_offsets):
        if po <= offset:
            page = i + 1
        else:
            break
    return page


def find_headings(text: str, page_offsets: list[int]) -> list[Heading]:
    headings = []
    for m in HEADING_RE.finditer(text):
        num = m.group("num").strip()
        title = (m.group("title") or "").strip()
        # filter false positives such as line numbers/items that have no title and are not target-like
        if num.isdigit() and int(num) > 10:
            continue
        headings.append(Heading(num=num, title=title, start=m.start(), page=page_for_offset(m.start(), page_offsets), level=clause_level(num)))
    headings.sort(key=lambda h: h.start)
    return headings


def next_boundary(headings: list[Heading], idx: int) -> int | None:
    current = headings[idx]
    for h in headings[idx + 1:]:
        if h.level <= current.level:
            return h.start
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a clause from the bundled ISO/FDIS 9001:2026 PDF.")
    parser.add_argument("clause", help="Clause number, e.g. 4.1, 6.3, 10.2, A.6.1.2")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Path to standard PDF")
    parser.add_argument("--include-annex", action="store_true", help="Allow Annex A extraction")
    parser.add_argument("--max-chars", type=int, default=8000, help="Maximum characters to print")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    parser.add_argument("--allow-external-pdf", action="store_true", help="Allow a PDF outside the skill bundle only after explicit user approval")
    parser.add_argument("--approval-text", default="", help="Required explicit user confirmation text for external PDF access")
    args = parser.parse_args()

    try:
        approval = {"external_access_approval": {"allowed": bool(args.allow_external_pdf), "approval_text": args.approval_text}}
        pdf_path = assert_path_inside_skill(args.pdf, purpose="clause extraction PDF", approval=approval)
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    text, page_offsets = build_text(pdf_path, include_annex=args.include_annex or args.clause.startswith("A."))
    headings = find_headings(text, page_offsets)
    target = args.clause.strip()
    matches = [h for h in headings if h.num == target]
    if not matches:
        available = ", ".join(h.num for h in headings[:80])
        raise SystemExit(f"Clause not found: {target}. Try search_standard.py. First headings: {available}")

    h = matches[0]
    idx = headings.index(h)
    end = next_boundary(headings, idx) or len(text)
    body = text[h.start:end].strip()
    truncated = len(body) > args.max_chars
    output = body[: args.max_chars].rstrip()
    if truncated:
        output += "\n...[truncated by --max-chars]"

    payload = {
        "source": str(pdf_path.relative_to(ROOT) if pdf_path.is_relative_to(ROOT) else pdf_path),
        "clause": h.num,
        "title": h.title,
        "start_page": h.page,
        "text": output,
        "truncated": truncated,
        "note": "Use for requirement verification and short audit criteria only; avoid long verbatim reproduction.",
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Source: {payload['source']}")
        print(f"Clause: {payload['clause']} {payload['title']}")
        print(f"Start page: {payload['start_page']}")
        print()
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
