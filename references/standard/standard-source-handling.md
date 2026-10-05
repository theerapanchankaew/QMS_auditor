# Standard Source Handling

## Placement
The published ISO 9001:2026 (Sixth edition, 2026-09) PDF is registered at:

`assets/standards/ISO_9001_2026.pdf`

It has an OCR text layer (`text_status: PDF text layer; not a full OCR
accuracy certification`). `scripts/controlled_retrieval.py` resolves it
through `assets/manifests/runtime-source-registry.json`, verifies its sha256,
and reads only the registered body pages (normative clauses 4–10; TOC and
Annex excluded). The earlier FDIS draft (`ISO_FDIS_9001_2026_en.pdf`) is a
historical source; a full-text comparison of all 65 clauses against it
(2026-10-05) found wording differences in 7 clauses — see
`assets/requirement_profiles/README.md`.

The standard navigation layer is bundled at:

- `references/standard/iso9001-2026-standard-map.md`
- `references/standard/iso9001-2026-clause-guide.md`
- `references/standard/iso9001-2026-definition-index.md`

## Workflow for real standard search
1. Use the standard map to identify the likely clause.
2. Use `scripts/extract_clause.py <clause>` to extract the clause text from the PDF when the clause is known.
3. Use `scripts/search_standard.py "<query>"` when the clause is unknown or the user asks about exact words/themes.
4. Use the extracted text only for requirement verification, clause matching, and short citations/summaries.
5. Avoid long verbatim reproduction. Summarize and cite clause numbers instead.

## Escalation triggers
Return `ReviewRequired` when:
- the PDF extraction is incomplete or ambiguous;
- the PDF appears to conflict with curated references;
- the user requests final certification or accreditation interpretation;
- the finding depends on exact wording and the script did not locate the relevant text;
- the task involves copyright-sensitive reproduction of long standard passages.

## Script examples

```bash
python scripts/search_standard.py "planning of changes" --max 10
python scripts/search_standard.py "ethical behaviour" --context 250
python scripts/extract_clause.py 6.3
python scripts/extract_clause.py 9.2
```
