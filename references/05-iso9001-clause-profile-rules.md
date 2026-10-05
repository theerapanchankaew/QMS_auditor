# ISO 9001 Clause Profile Rules

## Profile Purpose
Profiles guide reasoning style and evidence retrieval. They do not change ISO requirements.

| Profile | Use For | Reasoning Style |
|---|---|---|
| G4 | narrative, context, leadership, planning, management review, performance synthesis | semantic synthesis and contextual reasoning |
| B4 | checklists, approvals, release records, documented information, retained records, completeness checks | bounded completeness and field consistency |
| L4 | risk, change, supplier control, operation, NC, CAPA, traceability failure, exceptions | exception-biased and failure-focused reasoning |
| G3+R | constrained deployment after validation | implementation optimization only |

## Selection Rules
- Use G4 when evidence is mainly narrative or requires synthesis across context, leadership, policy, objectives, or review.
- Use B4 when the requirement is record-heavy or requires checking completeness of fields, approvals, dates, retention, or release evidence.
- Use L4 when the requirement is risk-heavy, exception-heavy, operationally sensitive, or related to change, supplier control, nonconformity, corrective action, or traceability.
- If multiple profiles apply, use the stricter profile for verification and disclose why.

## Clause Examples
- 4.1, 4.2, 5.1, 5.2, 6.2, 9.3 often need G4 synthesis.
- 7.5, 8.6, 8.7, 9.1 records often need B4 completeness checks.
- 6.1, 8.1, 8.4, 8.5, 10.2 often need L4 exception-sensitive reasoning.


## ISO 9001:2026 Clause Index

When ISO 9001:2026 is requested, use `references/data/iso9001_2026_clause_index.csv` as a concise clause-index and evidence-focus table. It supports clause mapping, checklist generation, evidence requests, and risk-sensitive sampling.

Do not treat the CSV as a replacement for the official standard. Use it as a working auditor guide first derived from FDIS-stage text; a full-text comparison of all 65 clauses (2026-10-05; see `assets/requirement_profiles/README.md`) found identical wording for 58 and wording differences in 7 (7.3, 7.5.2, 8.1, 8.3.2, 8.5.6, 8.6 and 9.2.2).
