# RAG Retrieval Rules

## Boundary
RAG retrieves and organizes evidence. RAG does not decide conformity.

## Retrieval Approach
1. Use clause and profile to define retrieval intent.
2. Retrieve evidence chunks or summarize supplied evidence.
3. Rank evidence by relevance, traceability, freshness, and directness.
4. Preserve evidence pointers.
5. Pass evidence to verification logic.

## Profile Behavior
- G4: retrieve broader narrative evidence and synthesize context.
- B4: retrieve records, fields, approvals, dates, and completeness buckets.
- L4: retrieve exceptions, failures, NC history, change records, supplier issues, CAPA, and traceability gaps.

## Weak Retrieval
If retrieval is weak or evidence is not supplied, do not guess. Return required evidence and likely clauses. Use `InsufficientEvidence` or `ReviewRequired` for material conclusions.

## Evidence Ranking Fields
Recommended ranked evidence fields:
- pointer
- source/title
- evidence type
- summary
- clause relevance
- freshness
- limitations
- exception flags, if any

## Full ISO 9001:2026 PDF Retrieval
For ISO 9001:2026 tasks, use the layered standard source structure:

1. Start with `references/standard/iso9001-2026-standard-map.md` to locate likely clauses.
2. Use `references/standard/iso9001-2026-clause-guide.md` for first-pass audit interpretation.
3. When exact wording is material, search or extract from the registered source `assets/standards/ISO_9001_2026.pdf` (resolved and sha256-checked by `scripts/controlled_retrieval.py`) using:
   - `python scripts/search_standard.py "<query>" --max 8`
   - `python scripts/extract_clause.py <clause>` — normative clauses 4–10 only. The TOC and Annex A are not indexed: `A.<clause>` / `--include-annex` return `ReferenceGap`; read Annex A from the user's own copy.
4. Preserve the script output fields: `source`, `source_sha256`, `start_page`/`end_page`, `clause`, snippet/`text`, truncation flag, and `text_status`.
5. Pass the exact requirement elements from the PDF to verification logic; do not let retrieval decide the verdict.

If PDF extraction is incomplete, ambiguous, or conflicts with curated references, return `ReviewRequired` and explain what must be manually checked in the official standard.

## Controlled retrieval boundary
For this skill, RAG means retrieval from bundled skill resources and user-provided evidence only. Do not retrieve from web search, public internet, external connectors, or prior model memory. If the needed source is not bundled or supplied by the user, return `outside controlled source scope` or `ReviewRequired` instead of filling the gap.
