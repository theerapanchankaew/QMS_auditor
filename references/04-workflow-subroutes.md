# Workflow Subroutes

Use these subroutes under `audit_workflow`.

## Subroutes

| Subroute | Trigger | Deliverable |
|---|---|---|
| `audit_program_planning` | annual/multi-site/program planning | program objectives, scope, frequency, risk focus |
| `audit_plan_preparation` | specific audit event | agenda, criteria, team, process schedule |
| `readiness_assessment` | stage 1, pre-audit, readiness | readiness status, gaps, evidence required |
| `checklist_generation` | checklist, questions, audit guide | clause/process-based checklist |
| `execution_support` | interview flow, onsite execution | audit questions, sampling, evidence prompts |
| `evidence_guidance` | what evidence to request | evidence list by clause/process |
| `nonconformity_drafting` | draft finding or NC statement | requirement, evidence, failure, wording |
| `audit_report_drafting` | draft report, conclusion | report sections, summary, conclusions |
| `ca_followup` | corrective action review | correction, root cause, CA, effectiveness review |
| `stage1_doc_review` | document review | documented information completeness |
| `gap_analysis` | gap analysis against ISO | mapped gaps, severity, evidence needed |
| `technical_review` | independent review | COV-based critique and review points |

## Standard Workflow Steps
1. Identify objective, scope, criteria, and process context.
2. Map relevant clauses and risk areas.
3. Determine evidence needed.
4. Apply sampling and AHP priority modifiers where useful.
5. Produce the requested deliverable using output templates.
6. Flag review-required items separately.

## v2 Corrective Action Follow-Up Rule
For `ca_followup` or any corrective action closure request, always provide a closure-oriented review using these mandatory elements:

1. **Correction adequacy** - Was the immediate problem corrected?
2. **Root cause adequacy** - Is the cause specific, systemic where needed, and supported by evidence?
3. **Corrective action adequacy** - Does the action address the cause rather than only remind people or restate the procedure?
4. **Effectiveness evidence** - Is there objective evidence that the issue has not recurred and the control works?
5. **Closure decision** - Use `Acceptable for closure`, `Not acceptable for closure`, or `InsufficientEvidence for closure`.
6. **Additional evidence required** - State the minimum evidence needed before closure.

Do not accept corrective action closure based only on correction, reminder, informal awareness, or undocumented intent.


## v3 Human Auditor Dialog Mode

When the user asks for dialog, interactive auditing, interview guidance, or human-auditor-style workflow, load `references/16-human-auditor-dialog-workflows.md`.

For each workflow output, include a `Dialog Script` or `Auditor Dialogue` section with:
1. Opening statement
2. Context confirmation questions
3. Evidence request questions
4. Probing questions
5. Interim summary language
6. Next action / escalation wording

Apply dialog mode to:
- audit plan preparation
- readiness assessment
- checklist generation
- execution support
- evidence guidance
- nonconformity drafting
- audit report drafting
- corrective action follow-up
- gap analysis and transition assessment

For ISO 9001:2026 transition/gap work, include questions on climate change relevance, quality culture and ethical behaviour, separated risks/opportunities, opportunity effectiveness, strengthened QMS change planning, organizational knowledge, and evidence protection.
