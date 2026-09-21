# Harness Integration — wiring the real G0–G7 harness into `aias_awm`

**Status: new, tested (6 new tests, `assets/tests/awm_v07/test_harness_integration.py`).
Closes the practical gap between this repo's two Audit World Model systems for
the deterministic-decision layer specifically — see "What is still NOT merged" below.**

## What this is

`scripts/awm_runtime/aias_awm/adapters/production_harness.py`
(`ProductionHarnessAdapter`) and
`aias_awm/control/decision_adapter.py` (`WorldToDecisionAdapter`) **already
existed** before this change — but nothing in this repo had ever actually
constructed a `ProductionHarnessAdapter` pointed at the real
`scripts/harness_gate_executor.py`, or called
`AuditWorldRuntime.make_decision()` at all (confirmed by grep: zero
call-sites anywhere, including every existing test and example script,
which all use `LegacyAIASHarnessStub` — a stub whose own docstring says
"Replace with the production AIAS G0-G13 deterministic harness").

This closes that: `ProductionHarnessAdapter` is now proven, by actually
running it, to load the real, unmodified
`scripts/harness_gate_executor.py` via `importlib` and delegate to its
real `enforce_gates(model_output: dict) -> dict` function — the exact same
function `python scripts/harness_gate_executor.py --input ...` uses from
the command line.

```python
from aias_awm.adapters.production_harness import ProductionHarnessAdapter
from aias_awm.runtime import AuditWorldRuntime

harness = ProductionHarnessAdapter("scripts/harness_gate_executor.py")
runtime = AuditWorldRuntime(db, harness, source_manifest_hash=..., rule_pack_hash=...)
...
decision = runtime.make_decision(case_id, candidate)  # candidate = a gate_execution_trace dict
```

## The layering this proves (Textbook Ch.13)

```
W0-W9 (world investigation) -> WG0-WG6 (decision readiness) -> real G0-G7 harness -> Human
```

`WorldToDecisionAdapter.decide()` evaluates `WG6` first. If the world
isn't decision-ready, it returns `{"status": "WORLD_NOT_DECISION_READY", ...}`
and **never calls the harness at all** — proven by
`test_decision_adapter_blocks_before_reaching_real_harness_when_world_not_ready`,
which asserts the result carries no `gate_validation` key (the one field
the real harness always sets). Only once `WG6` passes does the real,
unmodified G0–G7 harness run — proven by
`test_make_decision_through_full_runtime_reaches_real_harness_once_world_resolved`,
which goes through the entire real path
(`register_requirement` → `ingest_evidence` → `reason()` → `make_decision()`)
and gets back a genuine `gate_validation: PASS` from the actual harness
code, plus a genuine `FAIL` from `G3`'s real `D2_SAFE_LIST` (not a
re-typed copy of it) when a D2-safe clause is asked to carry a Major
verdict.

## What is still NOT merged

This wires the **decision/harness layer** of the two systems together. It
does **not** unify them structurally, and several things remain separate
by design:

- **The caller still builds the `gate_execution_trace` dict by hand.**
  Nothing here auto-derives `G0_preflight`/`G2_ie_chain`/
  `G3_severity_ceiling`/`G4_m4_conditions`/`G6_complied_check`/`G7_trace`
  from a `WorldSnapshot`/`RequirementAssessment`. That mapping is a
  separate, judgement-heavy task (e.g., what evidence in `aias_awm`'s
  model corresponds to `G6_complied_check.C3_elements_covered`?) not
  attempted here — inventing that mapping silently would risk encoding an
  incorrect semantic equivalence into a deterministic gate.
- **Bounded Imagination (`cognition/imagination.py`) and the older
  `scripts/imagination_engine.py`/`audit_world_model.py` remain separate**
  — this change only touches the decision/harness seam, not the
  simulation seam (see `references/69-bounded-imagination.md`).
- **The example scripts still construct `LegacyAIASHarnessStub`.** They
  don't exercise `make_decision()` at all (only `reason()`), so switching
  their harness choice wouldn't demonstrate anything new without also
  adding a `make_decision()` call — left as-is rather than making a
  cosmetic change that doesn't add real coverage.
- **`scripts/process_enforcer.py`'s S0–S11 state machine is still
  separate** from both `aias_awm`'s event-sourced state and the G0–G7
  harness call proven here. Nothing in this change wires it in.

## Usage

```bash
PYTHONPATH="scripts/awm_runtime;scripts" python -m pytest assets/tests/awm_v07/test_harness_integration.py -q   # 6/6
```
