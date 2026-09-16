# AIAS EEI Blueprint Crosswalk

**Status: maintainer/architecture reference only. Not loaded at runtime, not
part of the SKILL.md governance load order, and not cited by any route.**
Its only job is to stop this codebase from growing a second, parallel
implementation of logic that already exists — read it before proposing a
new top-level module for anything that sounds like "state machine",
"gate", "harness", "severity", "requirement atomization", or "evidence
classification".

## Why this file exists

On 2026-09-17 a review of `AIAS_EEI_Technical_Knowledge_Sharing.pptx` (a
technical knowledge-sharing deck, produced outside this repo — it is not
checked in here) proposed 10 "new" Python modules to bring this codebase in
line with an "AIAS EEI Blueprint": `requirement_atomizer.py`,
`evidence_classifier.py`, `sufficiency_tester.py`, `exception_validator.py`,
`corroboration_engine.py`, `impact_analyzer.py`, `severity_engine.py`,
`state_machine.py`, `gate_catalog.py`, `harness.py`.

Checking each one against the actual repo found that **4 of the 7 proposed
categories already exist**, already tested, under different names. Adding
parallel files for them would have created two competing implementations of
the deterministic assurance boundary — directly contradicting SKILL.md
BLOCK 3 Rule 24 ("harness enforces gates... never override the harness"),
since there would then be two harnesses with no defined precedence.

## Crosswalk table

| EEI Blueprint concept | Canonical implementation in this repo | Status |
|---|---|---|
| State machine S0–S11 | [`scripts/process_enforcer.py`](../scripts/process_enforcer.py) — `STATES` list, `check()` | **Implemented.** Labels match verbatim (`S0_RECEIVED`...`S11_MONITORED`). Also enforces state-skip prevention, `prediction_only` cannot advance past `S4_SUFFICIENCY`, `S10_RELEASED` requires `human_review_completed`. |
| Gate catalog G0–G7 + severity engine (M4 test, D2/D-safe ceiling) + harness (drift/forced-override) | [`scripts/harness_gate_executor.py`](../scripts/harness_gate_executor.py) — `D2_SAFE_LIST`, `M4_MANDATORY_LIST`, `enforce_g0_preflight`...`enforce_g7_trace`, `enforce_gates()`, `reject()` | **Implemented and unit-tested** (see the deploy pipeline's outlet-path tests). Produces `gate_validation: PASS/FAIL`, `rejection_reason`, `forced_overrides` — this is the EEI blueprint's "harness.py" `HarnessResult(admissible, forced_verdict, reason)` shape, already working. |
| A second, world-model-facing state/gate pair (not named in the EEI summary, but adjacent) | [`scripts/awm_runtime/aias_awm/control/world_fsm.py`](../scripts/awm_runtime/aias_awm/control/world_fsm.py) (`W0_UNINITIALIZED`...`W9_AUDIT_READY`) and [`control/world_gates.py`](../scripts/awm_runtime/aias_awm/control/world_gates.py) (`WG0`...`WG6`) | **Implemented — a separate, intentionally distinct numbering scheme** for the predictive/planning side (see SKILL.md BLOCK 3A). Do not conflate with S0–S11/G0–G7 (the assurance boundary), and do not add a third parallel scheme. |
| Evidence taxonomy (DIRECT/INDIRECT/CORROBORATED/CONFLICTING) + corroboration engine | [`domain/models.py`](../scripts/awm_runtime/aias_awm/domain/models.py) `EpistemicState` enum (11 values, including `CORROBORATED`/`CONTRADICTORY`) + `EvidenceItem.evidence_type` + `EvidenceExpectation.minimum_strength` (6-level ordinal: claim→documented→implemented→recorded→verified→effectiveness) + [`cognition/evidence_reconciliation.py`](../scripts/awm_runtime/aias_awm/cognition/evidence_reconciliation.py) `EvidenceReconciliationEngine` | **Implemented, at higher fidelity than the 4-bucket EEI taxonomy.** `CORROBORATED`/`CONTRADICTORY` already exist as literal states. There is no code gap here — at most a presentation-layer question (does a human-facing report need to print the literal words "DIRECT"/"INDIRECT"?), which is a rendering concern, not new reasoning logic. |
| Requirement atomization (AR schema) + sufficiency test (Q1–Q5) + breach detector | [`domain/models.py`](../scripts/awm_runtime/aias_awm/domain/models.py) `AtomicRequirement` (`requirement_id, clause, subject, obligation, object, condition, qualifier, semantic_category, evidence_expectations, failure_patterns, negative_inference_rules`) + [`cognition/requirement_engine.py`](../scripts/awm_runtime/aias_awm/cognition/requirement_engine.py) `RequirementStateEngine.assess()` | **Implemented.** `semantic_category` is literally `D2_SAFE \| M4_MANDATORY \| AMBIGUOUS` — the same severity-ceiling categories `harness_gate_executor.py` enforces. `assess()` already does not infer breach from mere absence of evidence (`breach_proven` requires explicit `proves_breach` metadata) — this is the same "missing evidence is not proven non-fulfilment" invariant SKILL.md BLOCK 9 states. |

## Naming collisions to watch for

1. **"Q1–Q5" means two different things in this repo already** — SKILL.md
   BLOCK 3 Rule 4 uses Q1–Q5 for the **exposure/severity trigger test**
   (product exposure → statutory breach → uncontrolled release → absent
   system element → recurrence, mapping to M1–M5). The EEI blueprint's
   Q1–Q5 is an **evidence sufficiency test** (relevant/valid/complete/
   reliable/consistent) — a different axis entirely. If either gets
   implemented as code, name it so the two are never confused in a trace
   or log line (e.g. `exposure_q1_q5` vs `sufficiency_q1_q5`).
2. Do not add a third S/G-style numbering scheme alongside S0–S11/G0–G7 and
   W0–W9/WG0–WG6.

## Confirmed genuine gaps (not yet built, deferred as of 2026-09-17)

These two are real — nothing in the repo implements them today:

1. **Applicability / conditional-qualifier evaluator** (EEI's
   `exception_validator.py`). `AtomicRequirement.applicability_rule_id`
   (`domain/models.py`) is a schema field with a matching SQL column
   (`sql/001_core_schema.sql`, `sql/002_cognitive_runtime.sql`) and JSON
   schema entry (`schemas/AtomicRequirement.schema.json`), but **nothing
   resolves it** — `RequirementStateEngine.assess()` takes `applicability`
   as an already-decided caller input; no code evaluates the "as
   applicable" / "as appropriate" qualifier itself. This is SKILL.md BLOCK
   3 Rule 3 (L7 Conditional Qualifier Gate), currently enforced by prompt
   instruction only, not by code. The natural home for this is a new
   method on `RequirementStateEngine` (or a sibling class in
   `cognition/`) that resolves `applicability_rule_id` → `applicability`
   *before* `assess()` runs — not a standalone parallel module.
2. **Impact/exposure scoring** (EEI's `impact_analyzer.py`, 5 dimensions:
   scope/effect/frequency/detection/recurrence). No decision table exists
   in code anywhere in `scripts/` or `scripts/awm_runtime/`. SKILL.md's Q1–
   Q5 exposure test (see collision note above) is the closest existing
   concept but is prompt-level, not a scored decision table.

Both are deferred pending explicit user sign-off — see project memory
`project_openwebui_deployment` / a follow-up decision — before writing new
code for either.
