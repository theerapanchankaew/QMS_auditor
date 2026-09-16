# Evidence Traceability Rules

Every material answer must preserve traceability from conclusion back to controlled source.

## Required trace fields

- `source_id`
- `source_title`
- `source_category`
- `controlled_location`
- `page`, `clause`, `section`, `line`, or `chunk_id` where available
- `retrieval_mode`: `bundled_only`, `uploaded_controlled_evidence`, or `approved_local_rag`
- `evidence_role`: definition, requirement, guidance, objective evidence, auditor workflow, or scoring rule

## Trace discipline

- Use source trace for facts and controlled interpretations.
- Label professional judgement separately from source facts.
- Do not cite broad files without indicating the relevant page, clause, or chunk when available.
- If trace is weak or missing, use `ReviewRequired` or `ReferenceGap`.
