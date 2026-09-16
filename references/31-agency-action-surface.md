# QMS Agency Action Surface

This reference defines what the QMS auditor skill may and may not do. The purpose is to make the action surface predictable and auditable.

## Allowed actions

| Action | Allowed condition |
|---|---|
| Search bundled references/assets | Only inside skill bundle. |
| Use approved local RAG | Only when declared in `assets/manifests/local-rag-connection-policy.json`. |
| Use uploaded evidence | Only when uploaded in the current task or explicitly provided as controlled evidence. |
| Run deterministic scripts | Only scripts inside `scripts/**` for validation, scoring, extraction, or packaging support. |
| Generate audit deliverables | Draft-only audit plans, checklists, reports, CA follow-up, conformity evaluations. |
| Generate `model_predictions.jsonl` | Only in benchmark mode from sanitized inputs. |
| Compute F1/performance | Only after joining hidden gold answer key with `model_predictions.jsonl` by `case_id`. |
| Generate HarnessCard/trace reports | For observability and repeatability. |

## Prohibited actions

- Do not search or browse the web.
- Do not use external connectors or public websites for QMS substance.
- Do not issue, approve, confirm, suspend, or withdraw certificates.
- Do not claim legal/regulatory/current accreditation status without uploaded controlled evidence.
- Do not invent objective evidence, audit records, interview statements, clauses, or source pointers.
- Do not expose hidden gold labels to model inference.

## Action normalization

When a requested action is prohibited, do not replace it with speculation. Return the allowed safe alternative: search bundled sources, analyze uploaded controlled evidence, ask for a controlled source upload, or return `ReferenceGap`/`ReviewRequired`.
