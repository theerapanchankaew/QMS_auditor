# Prediction / Evidence Separation Gate v1

## Purpose
Prevent predictive modules from contaminating the objective-evidence chain.

## Gate PE-1
Reject any material conclusion when any item used as decisive support has `epistemic_class=prediction_only`, `simulation=true`, or originates from a generated/imagined state without later corroborating evidence.

## Mandatory checks
1. Separate `observed_evidence[]` and `predicted_states[]`.
2. Verify every decisive assertion points to observed evidence.
3. Verify no embedding similarity score is cited as proof.
4. Verify simulated trajectories are absent from the evidence basis.
5. Verify G4 and G5 are rerun after new real evidence arrives.

## Decision
- PASS: predictions are used only for investigation planning.
- FAIL: prediction leakage into evidence or verdict reasoning.
- REVIEW: provenance cannot be determined.

## Relationship to core gates
PE-1 is an upstream integrity gate. It does not replace G4, G5, G10, G11, or G12.
