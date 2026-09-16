# AIAS Imagination Engine v1

## Purpose
Generate and compare bounded candidate audit trajectories inside the structured Audit World Model before interacting with the auditee.

## Core contract
`CURRENT_STATE -> CANDIDATE_ACTIONS -> IMAGINED_TRAJECTORIES -> POLICY_RANKING -> REAL AUDIT ACTION`

All imagined nodes must carry:
```json
{
  "simulation": true,
  "epistemic_class": "prediction_only",
  "evidence_status": "not_audit_evidence",
  "release_authority": "none"
}
```

## Trajectory rules
- Start only from a state grounded in observed evidence and controlled requirement sources.
- Generate no more than the configured horizon; default horizon is 3 actions.
- Keep branches explicit; never collapse mutually exclusive predicted outcomes into a single factual state.
- Model expected information gained, not a preselected finding.
- Stop a branch when the next step would require fabricated evidence or unsupported organizational facts.
- Prefer branches that resolve evidence sufficiency, contradiction, applicability, or systemicity uncertainty.

## Output
Each trajectory must include `trajectory_id`, `start_state_hash`, ordered actions, predicted state deltas, unresolved uncertainties, expected information gain, audit cost estimate, speculation risk, and `simulation=true`.

## Assurance boundary
Imagination output can recommend what to investigate next. It cannot satisfy G4 evidence sufficiency, G5 breach, G8 Major escalation, G10 provenance, G11 deterministic harness, or G12 human review.
