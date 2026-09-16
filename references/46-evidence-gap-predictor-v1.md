# Evidence Gap Predictor v1

## Purpose
Detect what should be investigated next without treating absence of evidence as evidence of nonconformity.

## Core invariant
`MissingEvidence != ProvenBreach`

## Required sequence
1. Determine the applicable atomic obligation.
2. Identify expected evidence classes for that obligation.
3. Compare observed evidence states with expected states.
4. Produce `gap_candidates` only.
5. Determine whether the evidence was requested, sampled, and corroborated.
6. Pass to G4 Evidence Sufficiency.
7. Only after G4 permits continuation may G5 evaluate fulfilment/breach.

## Gap object
```json
{
  "gap_id": "",
  "atomic_requirement_id": "",
  "expected_state": "",
  "observed_state": "",
  "expected_evidence_class": "",
  "gap_type": "missing|weak|stale|contradictory|not_sampled",
  "investigation_priority": 0.0,
  "candidate_audit_actions": [],
  "epistemic_class": "prediction_only",
  "breach_proven": false
}
```

## Hard stops
- If the only issue is that an expected record has not yet been requested, return an investigation action, not NC.
- If the sample is not representative for a systemic claim, prohibit M4 escalation.
- If the clause contains an applicability qualifier not yet resolved, follow the qualifier gate before gap interpretation.
