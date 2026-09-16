# AIAS Audit World Model Maturity and Validation v1

## Purpose
Provide a controlled maturity scale for claiming progress toward an Audit World Model.

## Levels
- **AWM-0 — LLM assistant:** prompt-response audit support; no explicit state model.
- **AWM-1 — Controlled state machine:** explicit states/gates and evidence boundary.
- **AWM-2 — Structured world representation:** Requirement, Evidence and Process worlds merged into AuditState.
- **AWM-3 — Coherent simulation:** bounded multi-step imagined trajectories plus compression/distinction coherence tests.
- **AWM-4 — Learned dynamics:** calibrated offline transition model with detour/OOD robustness and leakage-controlled trajectory dataset.
- **AWM-5 — Controlled adaptive audit agent:** learned policy improves audit action selection while all assurance conclusions remain under deterministic gates and human authority.

## Claim rule
Do not claim a higher level unless all lower-level controls remain active and regression-tested.

## Minimum AWM-3 acceptance targets
Use these as engineering targets, not certification criteria:
- unsupported-verdict rate = 0;
- prediction-to-evidence leakage = 0;
- forbidden-state-transition rate = 0;
- compression consistency >= 0.95 on controlled benchmark;
- distinction recall >= 0.90 on critical-state pairs;
- detour valid-continuation rate >= 0.90;
- all critical gate violations = 0.

## Current architectural target
AIAS v6.2 targets **AWM-3 architecture readiness**. AWM-4 requires real historical trajectory data, model training, calibration, and independent validation; it must not be claimed from architecture or synthetic tests alone.
