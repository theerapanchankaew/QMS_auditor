# Next Best Audit Action v1

## Objective
Rank practical audit actions that are most likely to resolve a material uncertainty while minimizing unnecessary audit effort.

## Candidate score
Use a transparent heuristic, not an opaque certification verdict:
`score = evidence_gain + requirement_coverage + contradiction_resolution + systemicity_value - audit_cost - redundancy - speculation_risk`

Normalize each component to 0..1 and record the components.

## Selection rules
- Prefer actions that resolve G4 sufficiency before severity analysis.
- Prefer primary evidence over policy statements when implementation is the issue.
- Prefer cross-checking contradictory sources before escalation.
- Prefer representative sampling when a systemic conclusion is contemplated.
- Never recommend an action whose sole purpose is to confirm a pre-selected verdict.

## Output
```json
{
  "recommended_action": "",
  "action_type": "request_document_or_record",
  "reason": "",
  "score_components": {},
  "expected_information_gain": "",
  "prediction_only": true
}
```
