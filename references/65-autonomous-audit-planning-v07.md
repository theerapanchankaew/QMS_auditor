# AWM v0.7 Autonomous Audit Planning Contract

## Purpose
Use transparent next-best-audit-action planning to reduce material uncertainty without granting autonomous verdict authority.

## Allowed planning outputs
The planner may propose and rank: `REQUEST_DOCUMENT`, `REQUEST_RECORD`, `ASK_INTERVIEW`, `OBSERVE_PROCESS`, `EXPAND_SAMPLE`, `TRACE_TRANSACTION`, `VERIFY_APPROVAL`, `VERIFY_VERSION`, `VERIFY_EFFECTIVENESS`, `CHECK_RECURRENCE`, `CROSS_CHECK`, `ESCALATE_HUMAN`, and `STOP`.

## Utility factors
Rank actions using explicit versionable factors: information gain, requirement coverage, expected evidence strength, contradiction reduction, temporal relevance, acquisition cost, and risk weight. Treat the score as planning utility only; it is not a conformity probability or audit sampling rule.

## Stop policy
Return one of:
- `CONTINUE` when material uncertainty remains and at least one admissible action exists.
- `STOP_DECISION_READY` when the world state is decision-sufficient.
- `STOP_BUDGET` when the configured audit-resource boundary is exhausted.
- `ESCALATE_HUMAN` when critical uncertainty remains but no permitted action can resolve it.

## Human authority
Do not execute external actions merely because the planner ranked them. Present proposed actions for auditor approval unless a separately authorized workflow explicitly permits execution.

## Evaluation
Track Next-Audit-Action Agreement and reciprocal-rank metrics against qualified-auditor acceptable actions. Maintain gold labels and adjudication separately from inference inputs.
