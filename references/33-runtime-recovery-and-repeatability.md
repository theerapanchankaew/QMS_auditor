# QMS Runtime Recovery and Repeatability

Use this reference to make QMS audit workflows bounded, recoverable, and repeatable.

## Runtime state machine

`START -> PREFLIGHT -> SCOPE_GATE -> SOURCE_INVENTORY -> ROUTE_SELECT -> CONTEXT_PACK -> EVIDENCE_MAP -> DECISION_GATES -> OUTPUT_VALIDATE -> TRACE_RECORD -> DONE`

## Recovery matrix

| Failure | Recovery |
|---|---|
| Missing controlled source | Return `ReferenceGap`; request upload. |
| Missing objective evidence | Return `InsufficientEvidence` or ask one focused question. |
| Unsupported Major trigger | De-escalate to Minor/OFI or `ReviewRequired`; state missing M-trigger evidence. |
| Conflicting evidence | Return `ReviewRequired` and list conflict. |
| Wrong standard/out of QMS scope | Return `OUT_OF_SCOPE`. |
| Invalid prediction schema | Normalize allowed values where safe; otherwise quarantine row. |
| Missing `case_id` | Quarantine row; do not score it. |
| Context overflow | Compact via context ledger; preserve source roles and evidence gaps. |

## Repeatability rules

- Keep route selection explicit.
- Keep verdict taxonomy fixed.
- Use deterministic scripts for scoring and validation.
- Preserve `case_id` exactly in benchmark workflows.
- Record decision trace for material QMS judgements.
- Report missing/extra predictions separately from score.
- Treat F1 drift as an upskill signal, not a direct conformity result.
