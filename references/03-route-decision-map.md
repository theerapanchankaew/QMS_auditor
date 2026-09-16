# Route Decision Map

## Routes

| Route | Use When | Output |
|---|---|---|
| `nc_classification` | User asks whether a finding is Major, Minor, OBS, OFI, or Not NC | classification, rationale, suggested wording, evidence needed |
| `predictive_risk_scoring` | User asks about audit risk, sampling, audit focus, process changes, repeated NC | risk score, risk drivers, sampling recommendation |
| `iso_clause_advisor` | User asks which clause applies to a process, evidence, statement, or issue | primary clause, related clauses, verification suggestions |
| `audit_workflow` | User asks for audit plan, checklist, report, evidence request, readiness review, CA follow-up | workflow deliverable |
| `conformity_evaluation` | User asks whether evidence meets ISO requirements | clause-by-clause verdict, confidence, missing evidence, escalation |
| `general_out_of_scope` | Request is not audit, ISO, management system, evidence, or certification related | safe redirect or limitation |

## Ambiguity Rules
Ask one clarification question when:
- The standard or clause is unknown and materially affects output.
- Evidence is referenced but not provided.
- The requested decision could be Major NC, certification-affecting, or high risk.
- The user mixes several tasks and the primary route is unclear.

Avoid unnecessary clarification for drafting tasks; make reasonable assumptions and state them.

## Multi-Route Requests
If a user asks for both checklist and clause mapping, perform the route that best supports the final deliverable and include secondary output briefly. For example, checklist generation may include clause mapping inside `audit_workflow`.


## ISO 9001:2026 Route Rules

When the user asks about ISO 9001:2026, FDIS 9001, transition, quality culture, ethical behaviour, separated risks/opportunities, opportunity-based thinking, strengthened management of change, climate change relevance, or organizational knowledge updates, load `references/15-iso9001-2026-requirements-guide.md`.

Route signals:
- “which clause”, “maps to what clause”, “interpret this requirement” -> `iso_clause_advisor`
- “does this comply”, “evaluate evidence”, “assess conformity” -> `conformity_evaluation`
- “audit interview”, “dialog”, “ask like auditor”, “conduct audit” -> `audit_workflow` with `references/16-human-auditor-dialog-workflows.md`
- “transition from 2015 to 2026”, “gap assessment” -> `audit_workflow.gap_analysis` or `conformity_evaluation` depending whether evidence is provided
- “classify finding” -> `nc_classification`

If the user asks for a human-auditor-style workflow, do not simply produce a checklist. Use staged dialogue with opening, focused questions, evidence requests, probing, interim summary, and next action.
