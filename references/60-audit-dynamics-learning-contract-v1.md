# AIAS Audit Dynamics Learning Contract v1

## Purpose
Define the learned component that estimates candidate audit-state transitions without gaining assurance authority.

## Dynamics interface
Estimate candidate state deltas using:
`D_theta(S_t, A_t) -> {DeltaS_(t+1), p, uncertainty}`

The output is planning information only. Never write directly to Evidence World or Assurance State.

## Learnable targets
Learn only non-authoritative transition tendencies such as:
- likely evidence class returned by an action;
- likely contradiction resolution path;
- likely information gain;
- likely sampling expansion need;
- likely process-interface dependency;
- likely next investigative branch.

Do not learn as authoritative targets:
- breach_proven;
- final conformity verdict;
- Major/Minor class;
- certification decision;
- gate pass/fail when deterministic inputs are available.

## Training data requirements
Use de-identified and governance-approved audit trajectories. Every training transition must separate:
- observed pre-state;
- actual auditor action;
- observed post-state;
- authoritative decision labels, if present, as evaluation-only fields;
- provenance and audit type;
- uncertainty and missing-data flags.

## Counter-shortcut training
Include multiple valid trajectories to the same state, distinct states with similar wording, rare detours, incomplete evidence, contradictory evidence, and negative examples. Avoid training only on successful or shortest audit paths.

## Calibration
Calibrate transition probabilities independently of verdict confidence. Poor calibration or out-of-distribution input must reduce planning authority and increase human-review preference.
