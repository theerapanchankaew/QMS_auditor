# World Constraint Validator — Evidence-Tagging Ambiguity Gate

**Status: advisory-only, unreviewed by a human auditor. Not validated
against this repo's 203-case synthetic corpus or `harness_gate_executor.py`'s
actual decisions for the same evidence — treat as a reasonable first
mapping, not a verified equivalence, until someone runs that comparison.**

## What this is

`scripts/world_constraint_validator.py` is a deterministic, stdlib-only,
dependency-free ambiguity gate for evidence tagging. It formalizes into
code a decision this repo's SKILL.md BLOCK 3 already makes in prose (rules
8, 14, 16–22): when a piece of evidence text is genuinely double-readable
— e.g. Thai `ไม่พบหลักฐาน` could mean `ABSENT` ("the process doesn't exist")
or unverified-`PRESENTED` ("the auditee's claim, not yet independently
checked") — the model should not silently pick one reading. This script
catches that fork mechanically instead.

It takes a list of candidate `(epistemic_state, coverage)` "world"
hypotheses for one evidence element (the LLM proposes the hypotheses; this
script only validates and compares them, it never invents a tagging
itself) and looks up each one's consequence in a fixed table:

```
|W| == 0            -> INCONSISTENT      -> FAIL_CLOSED
|W| == 1            -> UNIQUE            -> PROCEED
|W| > 1, |K| == 1   -> EQUIVALENT        -> PROCEED (different tags, same downstream path)
|K| > 1             -> MATERIAL_AMBIGUITY -> BLOCK_AND_CLARIFY, do not guess
```

(`W` = viable worlds, `K` = distinct consequences among them.)

It explicitly strips and reports any `confidence`/`likelihood`/
`probability`/`score`/`rank` field found on an input world — ambiguity is
resolved by evidence or human clarification, never by which reading
"sounds" more likely. Two of its 7 regression tests are adversarial cases
proving a smuggled confidence field cannot bias the result.

**Naming**: "world" here means a candidate evidence-tagging hypothesis
(possible-worlds semantics), unrelated to the W0–W9/WG0–WG6 Audit World
Model in `scripts/awm_runtime/aias_awm/control/` — different concept,
different directory. See the module docstring.

## What this does NOT do

- It does not compute a full audit verdict. Its consequence labels
  (`NC_CANDIDATE_PENDING_M1_M5_TEST`, `D1_MINOR_ANCHOR_CANDIDATE`,
  `COMPLIED_CANDIDATE`, `InsufficientEvidence`) are candidates, not
  verdicts — `harness_gate_executor.py`'s G0–G7 gates, the M1–M5 exposure
  test, and the M4 three-condition test still run afterward, unchanged.
- It does not touch `D2_SAFE_LIST`/`M4_MANDATORY_LIST` or any part of the
  existing deterministic harness.
- It has no corpus dependency and no learned component.

## Provenance

Ported from the **professional-auditor** Claude Skill (a separate,
independently-built ISO 9001:2026 reasoning system available in this
environment) via a patch series the user supplied
(`files.zip` → `0001-Port-AHP-engine-ambiguity-gate-and-IG-ranking.patch`).
The patch's own PR description disclosed it was drafted without a live
clone of this repo (`git clone`/`raw.githubusercontent.com` both failed —
this repo is private). Checking it against the real repo found:

- **This file did not collide with anything and is a faithful
  code-formalization of existing prose rules** — its `CONSEQUENCE_TABLE`
  was checked entry-by-entry against SKILL.md BLOCK 3 rules 16/17/19 and
  matches (e.g. `PRESENTED`+`covered` → `InsufficientEvidence` per rule 17;
  `VERIFIED`+`covered` → `COMPLIED_CANDIDATE` per rule 16). Its 7 tests
  were re-run independently in isolation after extraction and all passed.
  **Only this file and its test file were kept.**
- The rest of that same patch was **not** applied. It also proposed
  `scripts/ahp_engine.py`, which fully duplicates the existing, working
  `scripts/ahp_calculator.py` (principal eigenvector method, proper RI
  table, CI/CR, a finer-grained 3-tier consistency gate than the patch
  claimed to add) — and it tried to overwrite
  `scripts/next_best_audit_action.py`, `scripts/imagination_engine.py`,
  and `scripts/audit_state_canonicalizer.py` as brand-new files
  (`git apply --check` failed: "already exists in working directory")
  even though all three already exist here with real, working
  implementations tightly integrated with `audit_world_model.py` and
  SKILL.md's own governance vocabulary (`prediction_only`,
  `epistemic_class`, `release_authority`). Applying that part would have
  been destructive. See `docs/eei-blueprint-crosswalk.md` for the general
  pattern this fits — an external AI proposal authored without seeing this
  repo's actual code.

## Usage

```bash
python scripts/world_constraint_validator.py --input worlds.json
python scripts/world_constraint_validator_tests.py --run      # 7/7
```
