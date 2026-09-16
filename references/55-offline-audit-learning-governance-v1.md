# AIAS Offline Audit Learning Governance v1

## Purpose
Allow AIAS to learn planning heuristics from historical audit trajectories without converting model learning into certification authority.

## Permitted training corpus
Use de-identified, authorized historical sequences such as audit plan, question/action, evidence class, sampling decision, contradiction resolution, finding proposal, corrective-action follow-up, and human release outcome.

## Required separation
- Training labels may describe historical human outcomes, but runtime predictions remain `prediction_only`.
- Keep training, validation, blind evaluation, and runtime audit evidence stores separate.
- Never train directly on a current auditee's confidential evidence unless governance explicitly authorizes it.
- Do not perform autonomous online reinforcement learning against live auditees.
- A human-approved reward model may optimize information gain, requirement coverage, contradiction resolution, systemicity discrimination, audit efficiency, and speculation avoidance.

## Drift and release
Any new policy/world-model version must pass regression, leakage, prediction-evidence separation, and deterministic-harness tests before activation. Retain model version, rule-pack version, dataset version, and evaluation report in the immutable trace.
