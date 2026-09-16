# Structured Audit World Model v1

## Purpose
Model possible audit-state transitions without simulating raw documents or generating fictitious evidence.

## State formulation
Let `S_t` be a structured AuditState and `A_t` an AuditAction. The model estimates candidate next states:
`P(S_(t+1) | S_t, A_t)`.

## AuditState minimum fields
```json
{
  "case_id": "",
  "clause": "",
  "atomic_requirement_ids": [],
  "process_state": [],
  "evidence_state": [],
  "open_gaps": [],
  "contradictions": [],
  "sampling_state": {},
  "gate_state": {},
  "prediction_only": true
}
```

## Allowed AuditAction types
- ask_question
- request_document_or_record
- sample_record
- interview_role
- observe_activity
- trace_process
- cross_check
- expand_sample

## Forbidden action semantics
The world model may not:
- invent a record,
- assert that a predicted future state actually occurred,
- set a conformity verdict,
- set Major/Minor classification,
- bypass G4/G5/G8/G10/G12.

## Imagination / simulation use
Candidate trajectories may be ranked for information gain and audit efficiency. Every imagined state must remain explicitly tagged `simulation=true` until replaced by observed evidence.
