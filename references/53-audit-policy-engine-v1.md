# AIAS Audit Policy Engine v1

## Purpose
Select the next best real audit action from policy-safe candidate actions after imagination/simulation.

## Transparent objective
Use a bounded score:
`utility = evidence_gain + requirement_coverage + contradiction_resolution + systemicity_value - audit_cost - redundancy - speculation_risk`

Each component must be normalized to 0..1 and shown in the output. Do not hide the score components behind an opaque policy decision.

## Priority rules
1. Resolve applicability before testing breach when a conditional qualifier controls the requirement.
2. Resolve evidence sufficiency before severity.
3. Prefer primary evidence when implementation is disputed.
4. Cross-check contradictions before expanding severity.
5. Use representative sampling before a systemic conclusion.
6. Reject actions whose only rationale is to confirm a pre-selected verdict.
7. Escalate to the human auditor when two actions have materially similar utility but different audit consequences.

## Policy output
```json
{
  "recommended_action": {},
  "alternatives": [],
  "utility_components": {},
  "expected_information_gain": 0.0,
  "policy_reason": "",
  "prediction_only": true
}
```
