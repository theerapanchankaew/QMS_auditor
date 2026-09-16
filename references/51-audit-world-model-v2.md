# AIAS Structured Audit World Model v2

## Purpose
Create a structured, non-authoritative model of an audit environment so AIAS can reason about possible next states before requesting new evidence. This module does not simulate raw documents and does not create audit evidence.

## Three-world decomposition
1. **Requirement World** — controlled standard source, clause profiles, atomic requirements, qualifiers, applicability, severity anchors.
2. **Evidence World** — records, observations, interviews, performance data, external requirements, provenance, freshness, contradictions, and missing evidence.
3. **Process World** — process purpose, sequence, controls, roles, interfaces, inputs, outputs, monitoring, change, failure modes, and demonstrated implementation state.

The three worlds merge into one `AuditState` only through traceable identifiers. Never copy a prediction into the evidence world.

## Canonical state transition
Let `S_t` be a structured AuditState and `A_t` an allowed AuditAction. The world model may estimate candidate next states:

`P(S_(t+1) | S_t, A_t)`

The probability is a planning aid only. It is not evidence strength, confidence of conformity, or finding probability.

## AuditState v2
```json
{
  "case_id": "",
  "criterion": "ISO 9001:2026",
  "clause": "",
  "atomic_requirement_ids": [],
  "requirement_world": {
    "applicability": "not_assessed",
    "qualifiers": [],
    "required_evidence_classes": []
  },
  "evidence_world": {
    "observed_evidence_ids": [],
    "missing_evidence": [],
    "contradictions": [],
    "provenance_complete": false
  },
  "process_world": {
    "process_id": "",
    "implementation_state": "unknown",
    "control_points": [],
    "interfaces": [],
    "systemicity_state": "unknown"
  },
  "sampling_state": {},
  "assurance_state": {
    "state_machine_state": "S0_RECEIVED",
    "gate_state": {},
    "release_authority": "none"
  },
  "epistemic_class": "prediction_only"
}
```

## Allowed actions
- ask_question
- request_document_or_record
- sample_record
- interview_role
- observe_activity
- trace_process
- cross_check
- expand_sample

## Hard prohibitions
The world model must not invent a record, convert a simulation into observed evidence, set `breach_proven=true`, assign a conformity verdict, assign Major/Minor, bypass the deterministic harness, or release an audit conclusion.
