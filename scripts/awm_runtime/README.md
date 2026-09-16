# AIAS Audit World Model v0.7 — Autonomous Audit Planning

This release extends v0.6 with a controlled next-best-audit-action layer. The planner proposes evidence-acquisition actions but does not execute external actions or release audit verdicts. The existing AIAS deterministic gate kernel and human auditor remain authoritative.

## Added in v0.7

- Transparent information-gain / action-utility scoring
- Contradiction-targeted questioning
- Temporal / recurrence-aware sampling planner
- Stop / continue / human-escalation policy
- Planning persistence (`planning_runs`, `action_scores`)
- FastAPI planning and sampling endpoints
- Next-Audit-Action Agreement and Mean Reciprocal Rank metrics
- TII ISO 9001 Clause 6.1.3 autonomous-planning demonstration

## Planning utility

The v0.7 action scorer uses explicit, versionable factors:

`utility = f(information_gain, requirement_coverage, evidence_strength, contradiction_reduction, temporal_relevance, acquisition_cost, risk_weight)`

It is intentionally heuristic and inspectable; it is not reinforcement learning and it is not an audit sampling rule.

## New API endpoints

- `POST /api/v1/audits/{case_id}/plan`
- `POST /api/v1/audits/{case_id}/sampling/plan`

## Authority boundary

LLM / cognition may propose hypotheses and actions. The planning policy may rank them. It may not alter historical world state, verify evidence by assertion, bypass WG0–WG6 or G0–G13, or release conformity decisions.

## Tests

Validated locally with `pytest -q`: **31 passed**.

## Example

Run:

```bash
PYTHONPATH=. python examples/tii_613_autonomous_planning_demo.py
```

For the TII 6.1.3 unresolved-effectiveness example, the policy ranks `VERIFY_EFFECTIVENESS` ahead of a generic record request and returns `CONTINUE` while the world remains decision-insufficient.

## Roadmap to v0.8

The next release should implement the simulated audit environment / organization digital twin: explicit organization dynamics, action-observation transitions, counterfactual evidence acquisition, scenario trajectories, and planning-policy evaluation over multi-step episodes.
