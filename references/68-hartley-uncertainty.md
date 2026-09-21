# Hartley Uncertainty / Expected Information Gain

**Status: deterministic, tested, and wired into the runtime planner as of
2026-09-21. All 65 clauses now carry mechanically-derived possible-worlds
dimensions (see `assets/requirement_profiles/README.md`), and
`scripts/awm_runtime`'s planner uses a real `log2(k)`-bit measure instead of
its old heuristic constant whenever a hypothesis carries dimensions. See
"Update 2026-09-21" below for exactly what changed and what is still
deferred.**

## What this is

`scripts/hartley_uncertainty.py` is a deterministic, stdlib-only,
dependency-free calculator for two formulas:

```
Xt      = {x1, x2, ..., xk}      finite set of materially distinguishable
                                  feasible audit states at time t
H(Xt)   = log2|Xt|                Hartley measure, in bits
IG(a)   = H(Xt) - E[H(Xt+1) | a]  expected information gain of action a
```

It takes a set of named dimensions with enumerated possible values (e.g.
`implementation: [YES, NO]`, `effectiveness_evaluated: [YES, NO]`,
`objective_record: [PRESENT, ABSENT]`), builds the Cartesian product as `Xt`,
optionally narrows it by already-confirmed `known_facts`, and reports
`H(Xt)` in bits. In `--mode gain`, it additionally takes a set of candidate
action outcomes (each with a probability and the facts that outcome would
confirm) and computes `IG(a)`.

```bash
python scripts/hartley_uncertainty.py --input case.json --mode measure
python scripts/hartley_uncertainty.py --input case.json --mode gain
python scripts/hartley_uncertainty_tests.py --run      # 9/9
```

## Provenance

Built in response to a direct question about whether this repo's algorithms
are consistent with `AIAS_Theory_Technology_Stack_Textbook_v1.0.pdf` (a
MASCI-internal technical reference the user supplied, 29 pages, read in
full via PyMuPDF text extraction — not a paraphrase). That check found:

- A repo-wide search for `hartley`, `log2`, `entropy`, `cardinality`,
  `possible_worlds`, `bits` returned **zero hits** before this file existed.
- The textbook's Ch.9 worked example for **clause 6.1.3** — the same clause
  already used as this repo's own architecture-walkthrough example —
  computes `|X|=2x2x2=8` -> `H=log2(8)=3 bits`, and Ch.10 computes
  `IG(REQUEST_RECORD)=3-1=2 bits`. Nothing in the repo could reproduce
  either number.
- What the repo has instead is `expected_information_gain`, a bounded
  `[0.0, 1.0]` heuristic float, set either to a flat default (`0.60` in
  `scripts/awm_runtime/aias_awm/planning/scoring.py:53`) or a keyword-matched
  constant (`0.95 if "effectiveness" in ql else 0.80` in
  `scripts/awm_runtime/aias_awm/cognition/planner.py:40`), or supplied
  externally as a pre-computed `score_components.evidence_gain` value in
  `scripts/next_best_audit_action.py`. None of these derive uncertainty from
  an explicit enumeration of a finite possible-state set.
- The regression tests in `hartley_uncertainty_tests.py` transcribe the
  textbook's clause 6.1.3 dimensions verbatim and reproduce `H=3 bits` and
  `IG=2 bits` exactly, so this is a verified fix, not just plausible-looking
  arithmetic.

## What this does NOT do

- **It does not compute a verdict, severity, or breach determination.**
  `H=0` means the enumerated uncertainty has collapsed to one material
  state — it does **not** mean "conforming" (textbook Ch.9 Step 8, and
  `resolve_uncertainty()`'s own `reason` field says so explicitly when it
  fires).
- **It does not resolve which facts are known.** That is still evidence
  work done by the LLM extraction layer and, where a reading is genuinely
  ambiguous, `scripts/world_constraint_validator.py`.
- **It does not automatically populate `known_facts` from evidence.**
  `cognition/hypothesis_engine.py`'s `RuleBasedHypothesisEngine.update()`
  attaches a clause's `possible_worlds_dimensions` to a hypothesis when the
  caller supplies them, but leaves `known_facts` empty (`{}`) — there is no
  evidence-item-to-dimension-key mapping convention yet. Until one exists,
  every wired hypothesis starts from the clause's *full* raw uncertainty
  (`H(Xt)` with no facts narrowing it), not its true current state.

## Update 2026-09-21: wired into the runtime planner + all 65 clauses

Both items originally listed as deferred below are now done:

1. **All 65 clauses carry `possible_worlds_dimensions`.** Added to
   `scripts/build_requirement_profiles.py` as
   `compute_possible_worlds_dimensions()` — one binary dimension per
   `mandatory: true` evidence expectation already authored for that
   clause's elements, so no new per-clause domain judgement was invented
   (see `assets/requirement_profiles/README.md`'s new section for the
   exact rule and its caveat). Regenerated corpus verified purely additive
   (`git diff --stat`: only new keys inserted, zero deletions of existing
   content) and cross-checked against `scripts/hartley_uncertainty.py`
   directly on the real, regenerated `6.1.3.json` (`hartley_bits: 3.0`,
   matching the textbook exactly).
2. **Wired into `scripts/awm_runtime`'s planner, and into
   `scripts/next_best_audit_action.py`.** Because `expected_information_gain`
   is unbounded in bits but the existing schema bounds it to `[0, 1]`
   (`AuditAction.expected_information_gain`), the wiring uses
   `information_gain_from_resolving_dimension()`'s
   `normalized_information_gain = IG / H(Xt)` — "what fraction of the
   currently remaining uncertainty would resolving this one dimension
   remove" — rather than changing that bound. Concretely:
   - `scripts/hartley_uncertainty.py` gained
     `information_gain_from_resolving_dimension(dimensions, known_facts,
     target_dimension)`: an **exact** (not forecast-approximated) IG for
     fully resolving one named dimension, `IG = log2(k)` where `k` is that
     dimension's still-undetermined value count — a direct consequence of
     Hartley's independent-dimension Cartesian-product structure, proven
     by a regression test (`resolve_dimension_exact_ig_matches_log2_k`).
   - `scripts/awm_runtime/aias_awm/hartley.py` is a small, self-contained
     **port** of that same function (not an import — the package is
     installed independently and nothing in it imports a root `scripts/*.py`
     file; see that file's own docstring for why, and why it lives at the
     package's top level rather than inside `planning/` — putting it there
     recreated a `cognition`<->`planning` circular import).
   - `AuditHypothesis` (`domain/models.py`) gained two optional fields,
     `possible_worlds_dimensions` and `known_facts` — migrated consistently
     through the SQL table (`persistence/tables.py`), the hand-maintained
     JSON schema mirror (`schemas/AuditHypothesis.schema.json`, verified
     byte-for-byte against `AuditHypothesis.model_json_schema()`), and a
     round-trip test through real SQLite insert/select
     (`test_hypothesis_possible_worlds_dimensions_round_trip_through_sql`
     in `assets/tests/awm_v07/test_persistence_api.py`).
   - `cognition/hypothesis_engine.py`'s `RuleBasedHypothesisEngine.update()`
     gained an optional `dimensions_by_requirement` parameter (default
     `None` — existing callers unaffected).
   - `cognition/planner.py`'s `HeuristicAuditPlanner.propose()` now computes
     a real `log2(k)`-bit gain, normalized into `[0,1]`, whenever a
     hypothesis carries dimensions and its unresolved question is in the
     `"evidence_type:min_strength"` format `requirement_engine.py` produces
     (from which the exact target dimension name is derived); it falls back
     to the original `0.95`/`0.80` heuristic constant otherwise — verified
     by `test_information_gain_uses_real_hartley_measure_when_dimensions_present`
     in `assets/tests/awm_v07/test_planning_v07.py`, alongside the
     **pre-existing, unmodified** `test_information_gain_ranking_prioritizes_effectiveness`
     (no dimensions supplied) to prove the fallback path is unchanged.
   - `planning/scoring.py` needed **no change** — it already prefers
     `action.expected_information_gain` over its own flat default whenever
     the action supplies one, so it picks up the real value automatically.
   - `scripts/next_best_audit_action.py` gained an optional `"hartley"` key
     per candidate action (`{"dimensions", "known_facts",
     "target_dimension"}`); when present, it overrides
     `score_components.evidence_gain` with the real normalized gain,
     otherwise behavior is byte-for-byte unchanged from before.

Full existing regression suite re-run after every step
(`assets/tests/awm_v07/`, `PYTHONPATH=scripts/awm_runtime;scripts`):
**34/34 passed** (32 pre-existing + 2 new), plus
`scripts/hartley_uncertainty_tests.py` at **12/12**.

## Relationship to `world_constraint_validator.py`

Both files use "world" in the possible-worlds sense and both are
deterministic/stdlib-only, but they answer different questions:

| | `world_constraint_validator.py` | `hartley_uncertainty.py` |
|---|---|---|
| Question | Is this set of candidate evidence-TAGS safe to proceed on? | How much uncertainty (in bits) remains over an enumerated state set? |
| Output | A classification: UNIQUE / EQUIVALENT / MATERIAL_AMBIGUITY / INCONSISTENT | A quantity: `H(Xt)` in bits, or `IG(a)` in bits |
| Input probability rule | Confidence/likelihood on an evidence-tag is forbidden and stripped | A `known_facts` value must be a confirmed fact, never a confidence; an `action_outcomes` probability is a different, permitted use — the planner's own forecast of what an untaken action might reveal |

Neither imports the other. Do not merge them — see
`docs/eei-blueprint-crosswalk.md`, "Naming collisions to watch for", before
changing either.

## Deferred (not built here, needs explicit sign-off)

Both items originally listed here (authoring dimensions for all 65 clauses;
wiring the planner/scorer/`next_best_audit_action.py`) were completed on
2026-09-21 — see the Update section above. Still deferred:

1. **`known_facts` is never auto-populated from evidence.** No convention
   exists yet mapping a verified `EvidenceItem` to a specific dimension key
   (e.g. which evidence proves `AR-6.1.3-E02_record` is `"PRESENT"`).
   Without it, every wired hypothesis is scored from the clause's full raw
   uncertainty, not its true current state — this understates how much a
   clause has already been resolved by real evidence. Natural home: inside
   `cognition/requirement_engine.py`'s assessment logic, alongside
   `_missing_expectations()`.
2. A per-state contract requiring `H(Xt)` to be recorded before a case can
   leave `S4_SUFFICIENCY` in `scripts/process_enforcer.py` — plausible given
   the textbook's Ch.13 diagram, but this would be a behavior change to an
   existing, working gate and needs its own review.
3. `world_constraint_validator.py` remains intentionally unmodified — it
   answers a different question (evidence-tag ambiguity classification, not
   uncertainty magnitude); see "Relationship" below and
   `docs/eei-blueprint-crosswalk.md`'s "Naming collisions to watch for".
