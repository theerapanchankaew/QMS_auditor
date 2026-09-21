# Bounded Imagination — Simulation Firewall inside `aias_awm`

**Status: new, additive, tested (11 new tests, `assets/tests/awm_v07/test_imagination.py`).
A second, older, disconnected implementation of the same concept already
existed — see "Relationship to the older system" below before assuming
there is only one.**

## What this is

`scripts/awm_runtime/aias_awm/cognition/imagination.py` gives the
Pydantic/SQL-backed Audit World Model (`WorldSnapshot`,
`RequirementAssessment`, `AuditAction`) a counterfactual planning step
(Textbook Ch.11, "Bounded Imagination"): given a `WorldSnapshot` and a list
of candidate `AuditAction`s, `BoundedImaginationEngine.imagine()` produces
one `ImaginedTrajectory` per action — a predicted `RequirementAssessment`
for that action's target requirement, without touching any real state.

```python
from aias_awm.cognition import BoundedImaginationEngine
trajectories = BoundedImaginationEngine().imagine(snapshot, candidate_actions)
```

Wired into the runtime as a read-only method:

```python
result = runtime.imagine_actions(case_id)   # actions default to the case's real pending actions
# result["trajectories"] -- never persisted, snapshot/case state is untouched
```

## Simulation Firewall

Every `ImaginedTrajectory` carries four fixed, non-overridable markers
(dataclass fields with `init=False`):

```
simulation          = True
epistemic_class     = "prediction_only"
evidence_status     = "not_audit_evidence"
release_authority   = "none"
```

`imagine_one()`'s `predicted_delta` may only touch non-authoritative
`RequirementAssessment` fields (`coverage_ratio`, `missing_evidence`,
`positive_evidence_ids`, `negative_evidence_ids`,
`contradictory_evidence_ids`, `reasoning_candidate`). Attempting to set
`breach_proven`, `effectiveness_proven`, or `state` raises `ValueError`
immediately — verified by
`test_imagine_one_rejects_firewalled_field_breach_proven` and
`test_imagine_one_rejects_firewalled_field_state`.

`reject_if_simulated(candidate)` is an explicit guard any future
persistence or verdict boundary should call: it raises if `candidate` is
an `ImaginedTrajectory`/`ImaginedNode`, or any dict carrying
`simulation=True`.

## What this does NOT do

- **It never persists anything.** Neither `BoundedImaginationEngine` nor
  `AuditWorldRuntime.imagine_actions()` calls any repository's `upsert()`
  or emits a `WorldEvent`. Verified by
  `test_imagine_actions_through_runtime_has_no_side_effects_on_real_state`
  — assessment/hypothesis/action counts are asserted identical before and
  after calling `imagine_actions()`.
- **It does not forecast what evidence an action would actually surface.**
  Without a `predicted_delta`, the predicted assessment is simply the
  current one carried forward unchanged (or a synthetic
  `INSUFFICIENT_EVIDENCE` starting point if none exists yet) plus the
  firewall markers — this is a scaffold for exploring "what would the
  resulting assessment shape be if X", not a forecasting model. This
  matches the real capability level of the older system it parallels (see
  below), not an invented new capability.
- **It does not compute Hartley uncertainty or information gain.** See
  `aias_awm/hartley.py` and `cognition/planner.py` — a separate, unrelated
  concern this module does not duplicate or call.
- **It does not run the W0–W9/WG0–WG6 world gates** (`control/world_gates.py`)
  — those govern real decision readiness, not imagined exploration.
- **It does not evaluate whether the underlying snapshot is fresh.**

## Relationship to the older system (`scripts/audit_world_model.py` + `scripts/imagination_engine.py`)

A working Simulation Firewall already existed in this repo — but in a
**completely separate, disconnected** dict/JSON-based system at the
`scripts/` root, with no Pydantic models, no SQL persistence, and (verified
by grep, both directions) **zero cross-imports** with `aias_awm`. Actually
running it (not just reading it) confirmed it works: `audit_world_model.py`'s
`step()` strips `{'verdict','nc_class','trigger_or_anchor','breach_proven'}`
from the top level of any derived state and tags it with the same four
markers this file uses (`simulation`, `epistemic_class`, `evidence_status`,
`release_authority`) — see `docs/eei-blueprint-crosswalk.md`, "two separate
Audit World Model systems", for that investigation.

This file is **a fresh implementation of the same pattern**, not a port —
`RequirementAssessment` is a `StrictModel` (`extra="forbid"`) that cannot
carry the older system's loose dict-shaped simulation markers directly, so
those markers live on the `ImaginedTrajectory`/`ImaginedNode` wrapper
instead (plain dataclasses, never accepted by any repository's `upsert()`
by construction — a real, working type-boundary, not merely a naming
convention).

**Still two systems, not merged**: this closes the practical gap (a live
audit through `AuditWorldRuntime` can now do bounded imagination), but
`scripts/audit_world_model.py`/`imagination_engine.py` remain unmodified
and unconnected. Whether they should ever be unified is an open,
undecided question — not attempted here.

## Usage

```bash
python -m pytest assets/tests/awm_v07/test_imagination.py -q   # 11/11
```
