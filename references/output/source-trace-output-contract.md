# Source Trace Output Contract

For any answer using bundled or local RAG sources, include these sections or equivalent JSON fields:

## Human Auditor Frame
- mode: human_auditor_logic
- source boundary: controlled_sources_only
- retrieval mode: bundled_only / approved_local_rag / uploaded_controlled_evidence

## Controlled Sources Used
- source_id
- document title
- controlled location
- page/clause/chunk trace

## Source-Based Finding
State what the controlled source supports. Use concise paraphrase; do not reproduce long standard text.

## Auditor Judgement
State the professional interpretation separately from the source fact.

## Evidence Gaps / Next Audit Question
If evidence is missing, ask no more than three focused audit questions.

## Verdict
Use only: Informational, Complied, Noncomplied, OFI, OBS, InsufficientEvidence, ReferenceGap, ReviewRequired.
