# QMS Skill to Audit World Model Binding v1

## Trigger
Use this binding for `predictive_audit_assistance` and whenever the user asks the QMS Auditor to reason across evidence over time, maintain an audit-world state, identify unresolved requirements, investigate contradictions, detect recurrence, or recommend the next audit action.

## Execution order
1. Enforce the closed-source and scope controls.
2. Load applicable atomic requirement profiles and evidence rules.
3. Normalize source material to provenance-bearing evidence candidates.
4. Promote evidence only according to evidence-integrity rules.
5. Update the append-only audit world state and reconstruct the relevant as-of snapshot.
6. Calculate requirement states without collapsing missing evidence into breach.
7. Create or update audit hypotheses.
8. Rank next-best audit actions when material uncertainty remains.
9. Require WG0-WG6 decision readiness before entering the controlled decision path.
10. For material verdicts, run the existing layered cognition engine and G0-G13 deterministic harness.
11. Require human auditor confirmation before release.
12. Persist trace, feedback, and drift observations.

## Runtime invocation
Use `PYTHONPATH=scripts/awm_runtime` when executing the bundled package. Representative commands:

```bash
PYTHONPATH=scripts/awm_runtime python scripts/awm_runtime/examples/tii_613_autonomous_planning_demo.py
PYTHONPATH=scripts/awm_runtime python scripts/awm_runtime/examples/tii_613_replay.py
```

## Fallback when code execution is unavailable
Use the same schemas and authority boundaries conceptually, explicitly mark the result as a model proposal, and do not claim runtime execution, persistence, replay, or deterministic enforcement that did not occur.
