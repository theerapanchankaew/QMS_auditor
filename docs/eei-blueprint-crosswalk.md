# AIAS EEI Blueprint Crosswalk

**Status: maintainer/architecture reference only. Not loaded at runtime, not
part of the SKILL.md governance load order, and not cited by any route.**
Its only job is to stop this codebase from growing a second, parallel
implementation of logic that already exists — read it before proposing a
new top-level module for anything that sounds like "state machine",
"gate", "harness", "severity", "requirement atomization", or "evidence
classification".

## Why this file exists

On 2026-09-17 a first pass compared an assistant-produced *summary* of
`AIAS_EEI_Technical_Knowledge_Sharing.pptx` against this repo and proposed
10 "new" Python modules (`requirement_atomizer.py`, `evidence_classifier.py`,
`sufficiency_tester.py`, `exception_validator.py`, `corroboration_engine.py`,
`impact_analyzer.py`, `severity_engine.py`, `state_machine.py`,
`gate_catalog.py`, `harness.py`). That pass found 4 of 7 categories already
implemented and flagged 2 genuine gaps.

The same day, the actual `.pptx` (36 slides) was extracted with `markitdown`
and read directly. That corrected two things in the first pass:

1. The summary's own proposed "AIAS Runtime Stack v2.0" (`L1` Model Adapter
   at top, `L9` Harness/Governance at bottom) **does not match the deck's
   real stack** (slide 22: `1` Human Authority at top down to `7` Foundation
   Model at bottom — opposite direction, different layer boundaries). If a
   layer numbering is ever adopted in this repo, use the deck's L1–L7, not
   the fabricated L1–L9.
2. The state-machine and exception-test findings below needed correction
   once checked against the real slide content (slides 17, 18, 20, 26, 28,
   31) instead of the summary's paraphrase.

Slide 35 (Governance/PILOT status) independently confirms the intended
runtime is **"Open WebUI + Ollama", on-premise/self-hosted** — this matches
the `deploy/openwebui/` gateway already built in this repo.

## Crosswalk table

| EEI Blueprint concept | Canonical implementation in this repo | Status |
|---|---|---|
| State machine S0–S11 | [`scripts/process_enforcer.py`](../scripts/process_enforcer.py) — `STATES` list, `check()` | **Partially implemented — corrected after reading the real deck (slide 26).** S0–S5 match in intent (`RECEIVE→RECEIVED`, `PREFIX→PREFLIGHT`, `NORM→NORMALIZED`, `MAPPED→MAPPED`, `TEST READY→SUFFICIENCY`, `BREACH TEST→BREACH_TEST`). **S6–S11 diverge**: the deck's `S6 CORROBORATE, S7 IMPACT, S8 CLASSIFY, S9 REVIEW, S10 APPROVE, S11 RECORD` vs. the code's `S6_EXPOSURE, S7_SEVERITY, S8_GROUNDING, S9_HUMAN_REVIEW, S10_RELEASED, S11_MONITORED` are not the same sequence of checks. More importantly, slide 26 specifies **"State Contract = entry criteria + allowed action + exit criteria + failure route" per state** — the code has only ONE generic `check()` applied uniformly (state-skip prevention, `prediction_only` boundary, `human_review_completed` before `S10_RELEASED`), not 12 distinct per-state contracts. There is nothing today that requires corroboration output to exist before leaving S6, or impact-analysis output before leaving S7. This is a confirmed real gap — see below. |
| Deterministic harness drift rules (slide 33) + severity engine / M4 test (slide 32) | [`scripts/harness_gate_executor.py`](../scripts/harness_gate_executor.py) — `D2_SAFE_LIST`, `M4_MANDATORY_LIST`, `enforce_g3_severity_ceiling`, `enforce_g4_m4_conditions`, `enforce_g6_complied_check`, `enforce_g2_ie_chain` | **Implemented and unit-tested**, confirmed against the real deck. Slide 33's four pseudocode rules line up one-to-one: IE force from the IE chain → `enforce_g2_ie_chain`; D2_SAFE + Major → severity ceiling → `enforce_g3_severity_ceiling`; Major + M4 claimed without A∧B∧C → reject → `enforce_g4_m4_conditions`; Complied without all C1–C4 → force ReviewRequired → `enforce_g6_complied_check`. Slide 32's M4 test (A `process_entirely_absent` ∧ B `zero_records_in_verified_representative_sample` ∧ C `interview_confirms_systemic_absence`) matches the code's `enforce_g4_m4_conditions` field names almost verbatim. |
| Gate *outcome* vocabulary (slide 28: `PASS / HOLD / RETURN / ESCALATE / STOP`, each carrying reason code + evidence link + rule version + reviewer action) | `harness_gate_executor.py` only emits `gate_validation: PASS \| FAIL` (binary) with `rejection_reason`/`rejection_message`/`forced_overrides` and a free-text `action` hint | **Gap, narrower than first assessed.** The four drift-rejection *rules* are correct and implemented (row above); what's missing is the richer 5-way outcome vocabulary and structured `rule_version`/`evidence_link`/`reviewer_action` fields the deck specifies for every gate. Extension, not a new file: widen `reject()`'s return shape and give `enforce_gates()` a HOLD/RETURN/ESCALATE/STOP path in addition to PASS/FAIL. |
| A second, world-model-facing state/gate pair (not named in the EEI summary, but adjacent) | [`scripts/awm_runtime/aias_awm/control/world_fsm.py`](../scripts/awm_runtime/aias_awm/control/world_fsm.py) (`W0_UNINITIALIZED`...`W9_AUDIT_READY`) and [`control/world_gates.py`](../scripts/awm_runtime/aias_awm/control/world_gates.py) (`WG0`...`WG6`) | **Implemented — a separate, intentionally distinct numbering scheme** for the predictive/planning side (see SKILL.md BLOCK 3A). Do not conflate with S0–S11/G0–G7 (the assurance boundary), and do not add a third parallel scheme. |
| Evidence taxonomy (DIRECT/INDIRECT/CORROBORATED/CONFLICTING) + corroboration engine | [`domain/models.py`](../scripts/awm_runtime/aias_awm/domain/models.py) `EpistemicState` enum (11 values, including `CORROBORATED`/`CONTRADICTORY`) + `EvidenceItem.evidence_type` + `EvidenceExpectation.minimum_strength` (6-level ordinal: claim→documented→implemented→recorded→verified→effectiveness) + [`cognition/evidence_reconciliation.py`](../scripts/awm_runtime/aias_awm/cognition/evidence_reconciliation.py) `EvidenceReconciliationEngine` | **Implemented, at higher fidelity than the 4-bucket EEI taxonomy.** `CORROBORATED`/`CONTRADICTORY` already exist as literal states. There is no code gap here — at most a presentation-layer question (does a human-facing report need to print the literal words "DIRECT"/"INDIRECT"?), which is a rendering concern, not new reasoning logic. |
| Requirement atomization (AR schema) + sufficiency test (Q1–Q5) + breach detector | [`domain/models.py`](../scripts/awm_runtime/aias_awm/domain/models.py) `AtomicRequirement` (`requirement_id, clause, subject, obligation, object, condition, qualifier, semantic_category, evidence_expectations, failure_patterns, negative_inference_rules`) + [`cognition/requirement_engine.py`](../scripts/awm_runtime/aias_awm/cognition/requirement_engine.py) `RequirementStateEngine.assess()` | **Implemented.** `semantic_category` is literally `D2_SAFE \| M4_MANDATORY \| AMBIGUOUS` — the same severity-ceiling categories `harness_gate_executor.py` enforces. `assess()` already does not infer breach from mere absence of evidence (`breach_proven` requires explicit `proves_breach` metadata) — this is the same "missing evidence is not proven non-fulfilment" invariant SKILL.md BLOCK 9 states. |
| Bounded Imagination / Simulation Firewall (Ch.11, `AIAS_Theory_Technology_Stack_Textbook_v1.0.pdf`) — simulated trajectories tagged `simulation=true`, cannot set `breach_proven`/severity/verdict | Two implementations: [`scripts/imagination_engine.py`](../scripts/imagination_engine.py) + [`scripts/audit_world_model.py`](../scripts/audit_world_model.py) (older, dict-based) **and** [`scripts/awm_runtime/aias_awm/cognition/imagination.py`](../scripts/awm_runtime/aias_awm/cognition/imagination.py) (`BoundedImaginationEngine`, added 2026-09-21) | **Both implemented and tested; still two disconnected systems, now both closing the same practical gap.** The older one was re-verified by actually running it. The `aias_awm` one is a fresh implementation (not a port — `RequirementAssessment` is `extra="forbid"` and cannot carry the older system's loose dict markers), wired into `AuditWorldRuntime.imagine_actions()` as a read-only method (never calls `.upsert()`, verified by a test asserting assessment/hypothesis/action counts are unchanged before/after). See `references/69-bounded-imagination.md` and "Update 2026-09-21 (cont., 2)" below. |
| **Decision/harness seam between the two systems** — asked directly to merge them | [`scripts/awm_runtime/aias_awm/adapters/production_harness.py`](../scripts/awm_runtime/aias_awm/adapters/production_harness.py) (`ProductionHarnessAdapter`, pre-existing but never used) + [`control/decision_adapter.py`](../scripts/awm_runtime/aias_awm/control/decision_adapter.py) (`WorldToDecisionAdapter`, pre-existing but never called) + [`control/gate_trace_deriver.py`](../scripts/awm_runtime/aias_awm/control/gate_trace_deriver.py) (`GateTraceDeriver`, added 2026-09-21) | **Fully wired end-to-end, 2026-09-21**: `RequirementAssessment` → real `gate_execution_trace` candidate → real `WG6` readiness check → real, unmodified G0–G7 harness → result, via `AuditWorldRuntime.make_decision_for_requirement()`. See "Update 2026-09-21 (cont., 4)" below and `references/71-gate-trace-derivation.md`. **Still not a structural merge**: the derivation is fail-closed and conservative by construction (documented field-by-field), `process_enforcer.py`'s S0–S11 machine remains unwired, and Bounded Imagination's two implementations remain separate (`references/69-bounded-imagination.md`). |
| Hartley measure / expected information gain (Ch.9–10, `AIAS_Theory_Technology_Stack_Textbook_v1.0.pdf`) — `H(X)=log2\|X\|`, `IG(a)=H(Xt)-E[H(Xt+1)\|a]` | [`scripts/hartley_uncertainty.py`](../scripts/hartley_uncertainty.py) + [`scripts/awm_runtime/aias_awm/hartley.py`](../scripts/awm_runtime/aias_awm/hartley.py) (port) + [`scripts/requirement_profile_loader.py`](../scripts/requirement_profile_loader.py) | **Was a confirmed gap, closed 2026-09-21, wired into the planner the same day, then wired into the LIVE `reason()` pipeline the same day** after directly re-checking whether it actually reached that path (it didn't, at first — see "Update 2026-09-21 (cont.)" below). All 65 clauses carry mechanically-derived `possible_worlds_dimensions`; `AuditWorldRuntime.reason(..., dimensions_by_requirement=...)` now threads them from the real corpus through to a persisted, real `log2(k)`-bit `expected_information_gain`, proven by a live end-to-end test with zero evidence ingested (the realistic first-run case) — which also caught and fixed a real bug (planner only handled one of two unresolved-question string shapes `requirement_engine.py` actually emits). `known_facts` is still never auto-populated from evidence — remains deferred. |

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

Re-verified 2026-09-17 against the actual deck (36 slides, read via
`markitdown`). Grep-confirmed absent from `scripts/` and
`scripts/awm_runtime/`: `EXEMPTED`, `breach_status`, `exception_claimed`,
`compensating_control`, `effective_period_valid`, per-state `StateContract`/
`STATE_CONTRACTS`, and the `HOLD`/`ESCALATE` gate outcomes. Five gaps, not
two — the first pass under-counted because it conflated two distinct
concepts (see #1 vs #2 below) and hadn't seen the real deck's slides 20,
26, and 28.

1. **Exception Test / breach exemption** (slide 18) — *not* the same thing
   as applicability (#2). This is a 5-condition check run on an already-
   detected breach: `exception_defined_in_controlled_source`,
   `scope_matches_current_case`, `approval_authority_valid`,
   `effective_period_valid`, `compensating_control_present` → all true
   means `breach_status = EXEMPTED`, otherwise `CONFIRMED`. Nothing in the
   repo computes a `breach_status` at all today —
   `RequirementAssessment.breach_proven` is set directly from evidence
   metadata (`proves_breach`), with no expected-vs-observed-vs-exception
   test in between (slide 17's "Breach Test": `breach = observed violates
   expected AND no valid exception`). Natural home: a new method near
   `RequirementStateEngine`, run at the `S5_BREACH_TEST` step, not a
   standalone module.
2. **Applicability / conditional-qualifier evaluator** — separate from #1.
   `AtomicRequirement.applicability_rule_id` (`domain/models.py`) is a
   schema field with a matching SQL column and JSON schema entry, but
   **nothing resolves it** — `RequirementStateEngine.assess()` takes
   `applicability` as an already-decided caller input. This is SKILL.md
   BLOCK 3 Rule 3 (L7 Conditional Qualifier Gate — "as applicable"/"as
   appropriate"), currently prompt-only. Natural home: a method that
   resolves `applicability_rule_id` → `applicability` *before* `assess()`
   runs.
3. **Impact analysis** (slide 20; corrected field names from the real
   deck) — 5 dimensions: `Extent` (single point / multiple processes /
   whole system), `Consequence` (product / customer / system-outcome
   impact), `Duration` (one-time / continuous), `Detectability` (self-
   detected by controls or not), `Recurrence` (recurred and prior
   corrective action failed). No decision table exists anywhere in the
   repo. Note the deck's own caveat: "Impact score ใช้ช่วยจัดลำดับการทบทวน
   ไม่ควรแทน judgement ของผู้ตรวจประเมิน" — this must stay a
   review-prioritization aid, never a verdict input, if built.
4. **Per-state contracts for S0–S11** (slide 26) — see the state-machine
   row above. `process_enforcer.py` checks transition validity generically;
   it does not yet enforce that each state's specific entry/exit criteria
   were met (e.g., corroboration output present before leaving S6,
   impact-analysis output present before leaving S7). Natural home: extend
   `check()` / the `STATES` table in `process_enforcer.py` with a per-state
   criteria table, not a parallel state machine.
5. **Gate outcome vocabulary** (slide 28) — `PASS/HOLD/RETURN/ESCALATE/STOP`
   plus `reason code + evidence link + rule version + reviewer action` per
   gate. `harness_gate_executor.py` currently only returns
   `gate_validation: PASS|FAIL`. Extension: widen `reject()`'s return
   shape, not a new file.

Also worth a closer look later, not urgent: slide 31's "Evidence
Sufficiency Hard Stop" lists 5 checks (IE-1..IE-5); the existing
`enforce_g2_ie_chain` covers roughly 2 of them (the "ครบถ้วน สอดคล้อง" /
"ยืนยันการใช้งานจริง" steps) under different names. IE-4 ("sample scope
confirmed") doesn't appear to be checked anywhere. Not counted as a
numbered gap above since it may already be handled at the prompt/reasoning
level per SKILL.md refs 38/40/41 — needs a closer read of those references
before concluding it's a code gap, not just a documentation gap.

All five gaps above are deferred pending explicit user sign-off before
writing new code for any of them.

## Update 2026-09-17: full AtomicRequirement corpus authored

`assets/requirement_profiles/` now holds 155 `AtomicRequirement` records
across all 65 clauses tracked by this crosswalk (4.1–10.2.2), authored from
the real FDIS PDF text and validated against the real Pydantic schema. This
makes gap #2 (applicability) and the `semantic_category` question above
concrete with real numbers instead of a hypothetical: **25 of 65 clauses**
(6.1.3 among them) fall outside both `D2_SAFE_LIST` and `M4_MANDATORY_LIST`
and default to `AMBIGUOUS`. See `assets/requirement_profiles/README.md` for
full provenance, including a second AI-content source (the training-data
zip discussed elsewhere in project history) whose structural clause/element
inventory was reused but whose AI-adjudicated scenario/label content was
deliberately excluded for lack of SME attestation. Gaps #1, #3, #4, #5
above are unaffected — this corpus adds requirement content, not the
missing evaluators/contracts.

## Update 2026-09-17 (cont.): FDIS → published IS

> **Superseded 2026-10-05** — see the last section of this file. A full-text comparison of all 65 clauses found wording differences in 7 clauses (7.3, 7.5.2, 8.1, 8.3.2, 8.5.6, 8.6, 9.2.2); the "word-for-word identical" conclusion below was wrong for 7.5.2, 8.5.6 and 8.6.

ISO 9001:2026 was published (Sixth edition, 2026-09) after the above. The
corpus's `standard_id` now reads `"ISO 9001:2026"`; 21 of the 65 clauses
were sampled against the actual published-standard PDF (a scanned,
no-text-layer copy) by direct visual page comparison and came back
word-for-word identical to the FDIS text used above — see
`assets/requirement_profiles/README.md`'s "IS cross-check" section for the
exact clause list, the false-positive TOC finding caught and corrected
before it was reported, and what was deliberately left untouched
(`SKILL.md`'s source hierarchy, the checksummed
`bundled-source-manifest.json` entry, and `extract_clause.py`'s
`DEFAULT_PDF`, which must keep pointing at the FDIS file since it's the
only one with a working text layer).

## Update 2026-09-18: external patch from a sibling skill, mostly rejected

User supplied a git patch series (`files.zip`) claiming to port an AHP
engine, an evidence-ambiguity gate, and IG-weighted action ranking from
**professional-auditor** — a separate, independently-built ISO 9001:2026
Claude Skill available in this same environment, not this repo. Same
pattern this file exists to catch, now arriving as an actual patch instead
of pasted pseudocode: the PR description admitted it was drafted **without
a live clone of this repo** (`git clone`/`raw.githubusercontent.com` both
failed — repo is private).

Checked against the real repo before applying anything:

- `git apply --check` **failed** on 3 of the patch's files
  (`next_best_audit_action.py`, `imagination_engine.py`,
  `audit_state_canonicalizer.py`) — the patch encoded them as brand-new
  files (`--- /dev/null`), but all three already exist here with real,
  working implementations wired into `audit_world_model.py` and this
  repo's own governance vocabulary. Applying that part would have silently
  destroyed working code.
- The patch's `ahp_engine.py` fully duplicates the existing
  `scripts/ahp_calculator.py` (principal eigenvector method, proper RI
  table, CI/CR, and a finer-grained 3-tier consistency gate than what the
  patch claimed to newly add).
- **One piece checked out and was kept**:
  `scripts/world_constraint_validator.py` (+ its test file) — no file
  collision, its `CONSEQUENCE_TABLE` matches SKILL.md BLOCK 3 rules
  16/17/19 entry-by-entry, and its 7 regression tests were independently
  re-run after extraction and all passed. See
  `references/67-world-constraint-validator.md` for the full writeup.

Lesson for next time this happens: a patch file (vs. pasted text) is not
inherently more trustworthy just because it looks like a formal diff —
`git apply --check` plus reading the actual diff content is the same
verification this file already asks for, just applied to a different
input format.

## Update 2026-09-21: Hartley measure — confirmed gap, now closed

User supplied `AIAS_Theory_Technology_Stack_Textbook_v1.0.pdf` (29 pages,
MASCI internal technical reference) and asked whether this repo has any
algorithm inconsistent with it, specifically naming the Hartley measure and
clause profile. Read in full via PyMuPDF text extraction (not a paraphrase)
before answering.

**Clause profile**: no real gap. The textbook's abstract "R — Requirement"
world component (clause, atomic ID, applicability) matches the existing
`AtomicRequirement` schema and `assets/requirement_profiles/` corpus
already covered above, and `applicability` is already read by
`WorldGateEngine.evaluate()`'s `WG6` check.

**Hartley measure**: real, confirmed gap. `H(X)=log2|X|` and
`IG(a)=H(Xt)-E[H(Xt+1)|a]` (Ch.9–10) are the textbook's formal uncertainty
mechanism, worked through the *same* clause 6.1.3 example already used
elsewhere in this repo as an architecture-walkthrough case (`|X|=8` ->
`H=3 bits`; `IG(REQUEST_RECORD)=2 bits`). A repo-wide search for `hartley`,
`log2`, `entropy`, `cardinality`, `possible_worlds`, `bits` found nothing —
the closest existing mechanism, `expected_information_gain`, is a bounded
`[0,1]` heuristic (flat default, keyword-matched constant, or externally
supplied) with no cardinality/log2 computation anywhere behind it, in
`scripts/awm_runtime/aias_awm/planning/scoring.py`,
`cognition/planner.py`, and `scripts/next_best_audit_action.py`.

Closed by adding `scripts/hartley_uncertainty.py` (+ its 9-case regression
suite, which reproduces the textbook's own `H=3 bits`/`IG=2 bits` numbers
exactly) and `references/68-hartley-uncertainty.md`. Initially deliberately
additive-only (did not touch the three existing scorer files, did not
author dimensions beyond 6.1.3, did not merge with
`world_constraint_validator.py`).

**Same-day follow-up, explicitly requested**: the user asked to complete
the two items above ("wire the existing scorers" and "author dimensions
for the remaining 64 clauses"), plus re-quoted the reasoning for *not*
touching `world_constraint_validator.py` back as part of the same message —
read as context (it directly restates why that file is a different
question), not as a new instruction, since it would otherwise contradict
itself; `world_constraint_validator.py` was left unmodified.

Done:
- `scripts/build_requirement_profiles.py` gained
  `compute_possible_worlds_dimensions()` (one binary dimension per
  `mandatory: true` evidence expectation already authored per element — a
  mechanical rule, not new per-clause judgement) and now emits
  `possible_worlds_dimensions` for all 65 clauses. Regenerated corpus
  diffed as purely additive.
- `AuditHypothesis` gained `possible_worlds_dimensions`/`known_facts`,
  migrated through the SQL table, the JSON schema mirror (verified
  byte-identical to `model_json_schema()`), and a real SQLite round-trip
  test.
- `cognition/hypothesis_engine.py` and `cognition/planner.py` now compute a
  real `log2(k)`-bit gain when dimensions are present, falling back to the
  original heuristic otherwise (existing test unmodified and still
  passing, proving the fallback path).
- `planning/scoring.py` needed no change (already prefers the action's own
  `expected_information_gain`).
- `scripts/next_best_audit_action.py` gained an optional `"hartley"` block
  per candidate action, backward compatible when absent.
- Full suite re-run: `assets/tests/awm_v07/` **34/34** (32 pre-existing + 2
  new), `scripts/hartley_uncertainty_tests.py` **12/12**.

See `references/68-hartley-uncertainty.md` ("Update 2026-09-21") for the
full file-by-file writeup, including why `aias_awm/hartley.py` is a small
port rather than an import (a `cognition`<->`planning` circular import
otherwise), and what remains deferred (`known_facts` auto-population from
evidence; a per-state `S4_SUFFICIENCY` contract).

## Update 2026-09-21 (cont.): Hartley wiring only reached unit tests, not the live pipeline

Asked directly whether this repo's audit-state tracking and Hartley measure
both actually work, re-checking the real call chain (not just the tests
above) found that `reason()` (`aias_awm/runtime/service.py`) ->
`AuditCognitionPipeline.run()` -> `RuleBasedHypothesisEngine.update()` never
passed `dimensions_by_requirement` through — nothing in the live path
loaded `assets/requirement_profiles/` at all, so every real audit run would
still fall back to the old heuristic constant despite the wiring above.

Closed the same day: `AuditCognitionPipeline.run()` and
`AuditWorldRuntime.reason()` both gained an optional
`dimensions_by_requirement` parameter (default `None`), and new
`scripts/requirement_profile_loader.py` provides the caller-side glue —
kept outside `scripts/awm_runtime` for the same self-containment reason as
`aias_awm/hartley.py`, and filtering each requirement_id down to **only its
own element's dimensions** (not its whole clause's, which would inflate
`H(Xt)` for a question about one element of a multi-element clause).

Writing a live end-to-end test (real `register_requirement` ->
zero-evidence `reason()`, not a hand-built hypothesis fixture) caught a
real bug: `requirement_engine.py` emits an unresolved-question string in
two different shapes (`"evidence_type:min_strength"` when some evidence
exists but is insufficient, vs. a bare `"evidence_type"` with no colon when
none exists yet) — the planner wiring only handled the colon form,
silently falling back to the heuristic for the realistic zero-evidence
first-run case. Fixed in `cognition/planner.py`. Full suite re-run:
`assets/tests/awm_v07/` **35/35** (34 + 1 new).

## Update 2026-09-21 (cont.): two separate "Audit World Model" systems exist -- Bounded Imagination only lives in one of them

Asked directly whether audit state + audit world model can do Bounded
Imagination (textbook Ch.11). Checked by actually running both candidate
implementations, not just reading them:

- `scripts/audit_world_model.py`'s `step()` + `scripts/imagination_engine.py`
  (root `scripts/`, dict/JSON-based, no Pydantic, no SQL): ran a real
  state through both, end to end. Confirmed working: `FORBIDDEN_FIELDS =
  {'verdict','nc_class','trigger_or_anchor','breach_proven'}` are stripped
  from the top level of any derived state, every simulated state and
  trajectory is tagged `simulation:true` /
  `epistemic_class:prediction_only` / `evidence_status:not_audit_evidence`
  / `release_authority:none`, and `assurance_state` is explicitly
  deep-copied unchanged from the real input rather than derived by the
  simulation step — a real, working Simulation Firewall.
- `scripts/awm_runtime/aias_awm/` (the Pydantic/SQL-backed `WorldSnapshot`
  system this crosswalk has otherwise treated as *the* Audit World Model,
  and that all the Hartley-measure work above was wired into): grepped for
  `simulat|imagin|counterfactual|trajectory|bounded` across the whole
  package — **zero matches**. `cognition/planner.py` only proposes real
  next audit actions to actually take; nothing in this package generates
  or firewalls a counterfactual/simulated trajectory.

Cross-checked with a second grep in both directions: nothing under
`scripts/awm_runtime/` references `audit_world_model.py` or
`imagination_engine.py`, and nothing outside `scripts/awm_runtime/`
(besides this session's own new Hartley files, which only reference it in
doc comments, never a live import) references `aias_awm`. **These are two
fully disconnected systems**, not two views onto the same state. See the
new crosswalk table row above.

Practical consequence: a live audit run through
`AuditWorldRuntime.reason()` (the path this whole session's Hartley work
was wired into) has **no** bounded-imagination capability today. Getting
it would mean either (a) porting the older system's firewall pattern into
`aias_awm` as a new module, wired to real `WorldSnapshot`/`AuditAction`
types instead of the older loose dicts, or (b) formally documenting the two
systems as intentionally separate (root scripts = deterministic gate/
harness layer including this one capability; `aias_awm` = the stateful,
persisted, Hartley-aware planning layer) and deciding whether that split is
acceptable long-term. Neither decision was made here — this is a finding,
not yet a fix, pending the user's direction.

## Update 2026-09-21 (cont., 2): Bounded Imagination added to `aias_awm` (option (a) above, chosen)

User asked to actually build option (a): a real bounded-imagination module
inside `aias_awm`, not just documentation of the gap.

Added `cognition/imagination.py` — `BoundedImaginationEngine`,
`ImaginedNode`/`ImaginedTrajectory` (plain frozen dataclasses, not
`StrictModel`s, so they are never accepted by any repository's `upsert()`
by construction) and `reject_if_simulated()`. Firewall markers
(`simulation`, `epistemic_class`, `evidence_status`, `release_authority`)
are `dataclass` fields with `init=False`, matching the older system's
vocabulary exactly so a human or downstream tool sees the same four words
regardless of which system produced them. `imagine_one()`'s
`predicted_delta` is checked against `FIREWALLED_FIELDS =
{breach_proven, effectiveness_proven, state}` and raises `ValueError`
immediately if a caller tries to set one — verified by tests, including
through the live runtime call
(`test_imagine_actions_through_runtime_rejects_firewalled_predicted_delta`).

Wired into `AuditWorldRuntime` as `imagine_actions(case_id, actions=None,
predicted_deltas=None)` — read-only, defaults `actions` to the case's real
persisted pending actions, calls `rebuild_world()` for the real current
snapshot, and **never calls any repository's `.upsert()` or emits a
`WorldEvent`**. Proven, not just claimed:
`test_imagine_actions_through_runtime_has_no_side_effects_on_real_state`
asserts assessment/hypothesis/action counts are byte-identical before and
after calling it.

This is a **fresh implementation of the same pattern**, not a port of
`scripts/audit_world_model.py` — `RequirementAssessment` is `extra="forbid"`
and cannot carry the older system's loose dict-shaped markers directly.
The two systems remain disconnected; only the practical gap (a live audit
through `aias_awm` can now do bounded imagination) is closed, not the
architectural duplication itself — see
`references/69-bounded-imagination.md`, "Relationship to the older
system", for the explicit statement that unifying them is still an open,
undecided question.

Full suite re-run: `assets/tests/awm_v07/` **46/46** (35 + 11 new, all in
the new `test_imagination.py`).

## Update 2026-09-21 (cont., 3): merged the decision/harness seam — real G0–G7 harness now reachable from `aias_awm`

User asked directly to merge the two Audit World Model systems documented
above. Rather than rewriting either system (both have real, tested,
working code — the old harness's 155-case-style corpus discipline and the
new `aias_awm` package's SQL/event-sourcing), checked first whether an
integration seam already existed before building a new one.

It did: `aias_awm/adapters/production_harness.py`
(`ProductionHarnessAdapter`) and `control/decision_adapter.py`
(`WorldToDecisionAdapter`) were **already written**, with a docstring on
the stub it was meant to replace saying so explicitly ("Replace with the
production AIAS G0-G13 deterministic harness") — but grep confirmed
**zero call-sites anywhere** in the repo, including every test and example
script. This was designed-but-never-wired integration code, not a gap
requiring new architecture.

Closed by:

- Constructing a real `ProductionHarnessAdapter` pointed at the real,
  unmodified `scripts/harness_gate_executor.py` and driving real
  `gate_execution_trace` candidates through it — both directly and through
  the full `AuditWorldRuntime.make_decision()` path (register a real
  requirement, ingest real evidence, `reason()` to a real `SATISFIED`
  state, then `make_decision()`).
- Proving the layering `WG0–WG6 → real G0–G7 harness` actually holds: when
  the world isn't decision-ready, the harness is never invoked at all (the
  early-return result carries no `gate_validation` key — the one field the
  real harness always sets); once ready, the real harness runs and its
  real rejections come through unchanged (verified against the actual
  `D2_SAFE_LIST`, not a re-typed copy of it).
- New test file `assets/tests/awm_v07/test_harness_integration.py` (6
  tests, all passing). Full suite: **52/52** (46 + 6 new).

**Explicitly NOT done, to avoid inventing an unreviewed semantic mapping**:
nothing auto-derives a `gate_execution_trace` (`G0_preflight`/
`G2_ie_chain`/`G3_severity_ceiling`/`G4_m4_conditions`/
`G6_complied_check`/`G7_trace`) from a `RequirementAssessment` — the
caller still builds that dict by hand. Doing so would require deciding,
for example, what `aias_awm` evidence corresponds to
`G6_complied_check.C3_elements_covered`, which is a judgement call about
the real standard's requirements, not a mechanical translation — exactly
the kind of AI-authored semantic decision this repo's own governance
stance requires a human auditor to sign off on before treating as
authoritative. `process_enforcer.py`'s S0–S11 machine and the older
Bounded Imagination pair also remain unwired by this change — see
`references/70-harness-integration.md`, "What is still NOT merged".

## Update 2026-09-21 (cont., 4): auto-derivation built, on explicit reasoning that H1/H2/H3 remain final authority

User asked to build the auto-derivation "Update 2026-09-21 (cont., 3)"
explicitly declined, on the grounds that Textbook Ch.14's human
authorities (H1 Action Authorization, H2 Escalation Review, H3 Final
Release) remain the final word regardless of what any candidate proposes —
`gate_validation` is an input to human review, not a replacement for it.
Sound reasoning, but it doesn't make an overclaiming derivation harmless
(a misleading candidate can still bias a reviewer), so the module built —
`control/gate_trace_deriver.py::GateTraceDeriver` — stays fail-closed
throughout: every field defaults to the most conservative value unless a
precise, already-real, mechanical signal justifies otherwise (see
`references/71-gate-trace-derivation.md` for the full field-by-field
mapping table).

Key design choices worth flagging for future maintainers:

- `G0_preflight.closed_source_confirmed` maps to
  `WorldSnapshot.source_manifest_hash` being a real value — and
  `AuditWorldRuntime`'s own dev-mode default (`"DEV-SOURCE"`) deliberately
  does **not** count as confirmed. Proven meaningful, not just plausible:
  `test_derived_dev_placeholder_source_hash_is_rejected_by_real_g0` shows
  the real harness genuinely rejects it.
- The M4 test's A/B/C conditions have no clean mechanical equivalent in
  `aias_awm`'s existing fields (they describe systemic process absence, a
  different claim from "evidence exists proving a violation"). Rather than
  inferring them from an aggregate count, the deriver reads three new,
  **explicit opt-in** `EvidenceItem.metadata` keys
  (`process_entirely_absent`, `zero_records_in_sample`,
  `interview_confirms_absence`) that an upstream LLM/human step must set.
  Missing any one silently falls back to `Minor` — proven by two separate
  tests (all-three-present → real `Major` through the real `G4`; any
  subset → `Minor`, `G4` never even asked).
- `G2_ie_chain` (Thai-linguistic triggers) and `G3_severity_ceiling` are
  both deliberately left empty — the former because no equivalent data
  exists anywhere in `aias_awm`'s evidence model, the latter because the
  real harness already auto-detects it from `predicted_clause` against its
  own real lists, so filling it here would just be a second copy to keep
  in sync.

Every derived candidate in the test suite is submitted to the real,
unmodified `scripts/harness_gate_executor.py` and checked against its real
`gate_validation` result — including real rejections (an incomplete-
coverage `Complied` candidate is genuinely rejected by the real `G6`) — not
just checked against this module's own logic in isolation.

Full suite re-run: `assets/tests/awm_v07/` **73/73** (52 + 21 new, all in
the new `test_gate_trace_deriver.py`).

## Update 2026-10-05: registered published-edition PDF replaces the FDIS as the retrieval source

User asked to replace every use of the FDIS filename with `ISO_9001_2026`
and chose to adopt the retrieval design from their own evolved copy of this
repo (`QMS_Auditor.rar`, read as data; only the pieces below were taken).

**Why a rename was not enough.** `assets/standards/ISO_9001_2026.pdf` is the
published Sixth edition (sha256 `346ce2e9…`, 48 pages) with an **OCR** text
layer. Pointing the old `extract_clause.py` at it returned 13–60 characters
for 40 of the 65 clauses and nothing for 7.5.3.2 / 8.7.2 (different line
structure; running headers `ISO 9001:2026(en)`; Annex A starts on page 35,
not the hard-coded 38). A string replace would also have broken facts: the
manifest checksum (`71252005…`), the 157 FDIS-paginated RAG chunks and every
doc sentence saying "the bundled source is FDIS-stage text".

**Taken from the RAR (user's own code/data):**
`scripts/controlled_retrieval.py` (`ClauseStore`: sha256-bound, registered body
pages 15–34, coordinate-based header/footer exclusion, heading integrity
checks), `assets/manifests/runtime-source-registry.json` (incl. the
`23:7.8.3 → 7.5.3` OCR heading correction), the new thin
`scripts/extract_clause.py` / `scripts/search_standard.py` (our previous
extractor is kept as `scripts/extract_clause_legacy.py`, still FDIS-based),
the manifest layout (`iso9001-2026-user-pdf` active; the FDIS and ISO 9000
sources under `unavailable_historical_sources`; the pre-switch manifest kept
as `historical-source-manifest.json`) and the `is_relative_to` fix in
`source_manifest_validator.py`. **Not taken:** `service/`, `gate_runner.py`,
`strict_gate_contract.py`, deployment/test scripts, the profile `review`
structure and approval records — out of scope.

**Decisions to be aware of (all reversible):**
- ISO 9000 FDIS + glossary are no longer in the active manifest (as in the
  RAR). The two ISO 9000 reference docs now say so; terminology needing them
  → `ReferenceGap` unless supplied as controlled evidence.
- The RAR retires the local-RAG profile (`approved_profiles: []`). Here it
  was kept **approved** and the index **rebuilt** from the new manifest
  (`allowed_source_ids`: `iso9001-2026-user-pdf`, `qms-curated-references`;
  145 + 557 chunks), because the request was for the RAG index to point at
  the new PDF. `standard_index_builder.py` now writes POSIX paths (a rebuild
  on Windows had produced backslashes).
- `extract_clause.py` lost `--allow-external-pdf` / `--approval-text`; it
  refuses any PDF other than the registered one, and Annex A / TOC are not
  retrievable (`ReferenceGap`).
- `references/data/iso9001_2026_pdf_clause_pages.csv` and the clause index
  (renamed `clause_index_iso_9001_2026.json`) carried FDIS page numbers
  (clause 4.1 on p.17; it is p.15 in the IS). Both were regenerated from the
  registered PDF; Annex A sub-entries and clauses 1–3 are located by heading
  search / approximated (noted in the file).

**Finding — the FDIS and the published text differ.** Full-text comparison of
all 65 clauses (legacy FDIS extraction vs `ClauseStore`, normalised): 58
identical, 7 differ in wording (7.3, 7.5.2, 8.1, 8.3.2, 8.5.6, 8.6, 9.2.2;
4 confirmed on the IS page images, 3 from the OCR layer only). This
**invalidates** the 2026-09-17 visual sample that recorded 21 clauses as
word-for-word identical (wrong for 7.5.2, 8.5.6, 8.6). Three requirement
elements quoted a changed phrase and were updated ("conformity with" →
"conformity to": AR-7.3-E01, AR-8.5.6-E01, AR-8.6-E03); `9.3.2` gained a
`6.1.3` explicit reference the old extractor had missed. Curated guides
(`references/15`, `clause-guide`, `standard-map`, CSV index) were first
written from the FDIS and now say so, with the 7-clause caveat. Details:
`assets/requirement_profiles/README.md`.

**Verification:** `assets/tests/test_controlled_retrieval.py` (16 tests: hash
binding, all 65 clauses retrievable inside the registered pages, annex /
unregistered-PDF refusal, manifest–registry–index–profile consistency),
`run_regression_suite.py` 48/48, `assets/tests/awm_v07/` 74/74,
`source_manifest_validator.py` valid. The OCR layer carries no accuracy
certification (`text_status`); single-word findings still need a licensed
copy.
