# Gate Trace Derivation — `RequirementAssessment` → real G0–G7 candidate

**Status: new, tested (21 tests, `assets/tests/awm_v07/test_gate_trace_deriver.py`,
including live execution against the real, unmodified `scripts/harness_gate_executor.py`).
Fail-closed by construction — see "What this does NOT do" before relying on any single field.**

## Why this exists

`references/70-harness-integration.md` wired `aias_awm`'s decision layer to
the real G0–G7 harness, but deliberately stopped short of building this:
the harness's `enforce_gates(model_output: dict)` needs a hand-built
`gate_execution_trace` dict, and inventing the mapping from
`RequirementAssessment`'s fields to that trace risked silently encoding an
unreviewed judgement about what the standard requires into a deterministic
gate.

Asked to build it anyway, with the reasoning that Textbook Ch.14's human
authorities (**H1** Action Authorization, **H2** Escalation Review, **H3**
Final Release) remain the final word regardless of what any candidate
proposes — `gate_validation` is an input to human review, never a
replacement for it. That reasoning is sound, but it does not make an
overclaiming derivation harmless (a misleading candidate can still bias a
reviewer or waste their time), so `GateTraceDeriver`
(`scripts/awm_runtime/aias_awm/control/gate_trace_deriver.py`) is
**fail-closed throughout**: every field defaults to the most conservative
value (`ABSENT` / `False` / `InsufficientEvidence` / `Minor`) unless a
precise, already-real, mechanical signal in `aias_awm`'s own data model
justifies otherwise.

## Field-by-field mapping

| Harness field | Derived from | Rule |
|---|---|---|
| `predicted_clause`/`clause` | `AtomicRequirement.clause` | direct |
| `verdict` | `RequirementAssessment.state` | table below |
| `G0_preflight.closed_source_confirmed` | `WorldSnapshot.source_manifest_hash` | `True` only if set to a real, non-placeholder value (`"DEV-SOURCE"` — `AuditWorldRuntime`'s own dev default — and `""` both count as **not** confirmed) |
| `G1_linguistic.evidence_activity` | strongest `EpistemicState` among this requirement's evidence | `VERIFIED`/`CORROBORATED` → `VERIFIED`; `PRESENTED`/`CLAIMED`/`PARSED` → `PRESENTED`; `PARTIAL` → `PARTIAL`; everything else (`CONTRADICTORY`/`INVALID`/`STALE`/`SUPERSEDED`/`UNKNOWN`/no evidence) → `ABSENT` |
| `G2_ie_chain` | — | **left empty.** No Thai-linguistic-trigger data (`ครบถ้วน สอดคล้อง`, `ยืนยันการใช้งานจริง`, etc.) exists anywhere in `aias_awm`'s evidence model — honestly not derived, not guessed |
| `G3_severity_ceiling` | — | **left empty deliberately.** `enforce_g3_severity_ceiling` already auto-detects `clause_category` from `predicted_clause` against its own real `D2_SAFE_LIST`/`M4_MANDATORY_LIST`/`AMBIGUOUS_LIST` — filling it here would just be a second, redundant copy to keep in sync |
| `nc_class` (when `verdict=="Noncomplied"`) | `AtomicRequirement.semantic_category` + opt-in evidence metadata | `D2_SAFE`/`AMBIGUOUS` → always `Minor`. `M4_MANDATORY` → `Major` **only** when evidence metadata explicitly carries all three of `process_entirely_absent`, `zero_records_in_sample`, `interview_confirms_absence` (new opt-in convention, see below); otherwise `Minor` |
| `G4_m4_conditions` | same opt-in metadata | filled only in the all-three-true case above; empty otherwise |
| `G6_complied_check` (when `verdict=="Complied"`) | `RequirementAssessment`/`EvidenceItem` | `C3_elements_covered` = `coverage_ratio == 1.0` (exact); `C1_implementation_proven` = a positive evidence item has `evidence_type=="observation"`; `C2_record_proven` = a positive evidence item has `evidence_type` in `{record, measurement, system_log}`; `C4_evidence_current` = at least one positive evidence item exists and none are `STALE` |
| `G7_trace.decisive_question` | `AtomicRequirement.subject/obligation/object/clause` | a deterministic template, always present |

### `verdict` table (from `RequirementAssessment.state`)

| State | Verdict |
|---|---|
| `SATISFIED` | `Complied` |
| `BREACH_PROVEN` | `Noncomplied` |
| `INSUFFICIENT_EVIDENCE`, `PARTIALLY_SUPPORTED`, `UNKNOWN` | `InsufficientEvidence` |
| `CONTRADICTORY`, `REVIEW_REQUIRED` | `ReviewRequired` |
| `NOT_APPLICABLE` | `OUT_OF_SCOPE` |

## The M4 opt-in metadata convention

The M4 test's A/B/C conditions (`process_entirely_absent`,
`zero_records_in_sample`, `interview_confirms_absence`) describe **systemic
absence of a process** — a materially different claim from "evidence
exists proving a violation" (the far more common `breach_proven` case).
Nothing in `aias_awm`'s structured fields distinguishes these, so rather
than inferring systemic absence from an aggregate count (e.g. "zero
positive evidence items" — fragile and easy to get wrong), the deriver
reads three new, optional `EvidenceItem.metadata` keys that an upstream
LLM/human step must set **explicitly**:

```python
metadata={"proves_breach": True, "process_entirely_absent": True,
          "zero_records_in_sample": True, "interview_confirms_absence": True}
```

Missing any one of the three silently and safely falls back to `Minor` —
proven by `test_nc_class_defaults_minor_for_m4_mandatory_without_opt_in_flags`
and `test_nc_class_minor_when_only_partial_opt_in_flags_present`.

## What this does NOT do

- **It is not an SME-authored interpretation of ISO 9001.** Every mapping
  above reads a structural fact already present in `aias_awm`'s own model
  (`coverage_ratio`, `evidence_type`, `epistemic_state`,
  `source_manifest_hash`, `semantic_category`) or an explicit opt-in flag —
  it does not decide what the standard requires.
- **It does not derive G2's Thai-linguistic triggers at all.** That still
  requires the LLM extraction/reasoning layer (SKILL.md BLOCK 3) or
  `world_constraint_validator.py`.
- **It never overrides the real harness's own decision.** Every derived
  candidate still goes through the actual, unmodified
  `scripts/harness_gate_executor.py::enforce_gates()` — proven by tests
  that submit derived candidates to the real harness and check its real
  `gate_validation` (including real rejections: an incomplete-coverage
  `Complied` candidate is really rejected by the real `G6`, not just by
  this module's own logic).
- **It does not replace human review.** `AuditWorldRuntime.make_decision_for_requirement()`
  echoes the full derived candidate back as `derived_candidate` in its
  result specifically so a reviewer can see exactly what was derived and
  why, not just a black-box `PASS`/`FAIL`.
- **It does not touch `process_enforcer.py`'s S0–S11 machine**, and it
  does not interact with Bounded Imagination (`cognition/imagination.py`)
  — see `references/70-harness-integration.md` for what else remains
  unmerged between the two systems.

## Usage

```python
from aias_awm.control import GateTraceDeriver
candidate = GateTraceDeriver().derive(
    assessment=assessment, requirement=requirement,
    evidence_items=evidence_items, snapshot=snapshot,
)
```

Or, through the runtime (loads everything from the real DB automatically):

```python
decision = runtime.make_decision_for_requirement(case_id, requirement_id)
# decision["gate_validation"], decision["derived_candidate"]
```

```bash
PYTHONPATH="scripts/awm_runtime;scripts" python -m pytest assets/tests/awm_v07/test_gate_trace_deriver.py -q   # 21/21
```
