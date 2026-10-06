# 72 — L7 Conditional Qualifier Gate: enforcement (gateway harness + AWM)

Status: implemented 2026-10-06. Spec of the gate itself: `26-layered-audit-cognition.md` § L7 and SKILL.md rule 3. Routing code: `scripts/conditional_qualifiers.py` (`l7_route`). This page says **where the gate is enforced and what it does not do**.

## 1. Two enforcement points, one routing function

| Path | Where | Input source | Effect |
|---|---|---|---|
| Gateway (OpenWebUI) | `scripts/harness_gate_executor.py`, gate `L7` (order G0, L7, G2, G3, G4, G6, G7); `outlet()` already runs the harness on the model's `gate_execution_trace` | the model's `L7_conditional_qualifier` section | reject + forced verdict |
| AWM | `aias_awm/control/gate_trace_deriver.py` using `aias_awm/qualifiers.py` (parity copy of the script, drift-tested) | `AtomicRequirement.qualifier` + opt-in evidence metadata | derived verdict follows the route; derived trace is then passed to the real harness |

`aias_awm` must stay independently installable, hence the parity copy (`assets/tests/awm_v07/test_l7_awm.py` fails if phrase→family tables or routing diverge from the script).

## 2. Harness behaviour

Conditional clause = the 22 inventory clauses (`QUALIFIER_CLAUSES`) + 8.3 / 8.3.x + 8.5.3 + 8.5.5 (`is_conditional_clause`).

| Situation | Rejection | Forced verdict |
|---|---|---|
| `Noncomplied` on a conditional clause, no section | `L7_NOT_RUN` | ReviewRequired |
| section malformed (non-object, empty / non-canonical `phrases`, non-bool `condition_evidenced`, bad `determination` / `a3_effect` / `justification`) | `L7_TRACE_INVALID` | ReviewRequired |
| route `OFI_STOP`, verdict ∉ {OFI, ReviewRequired} | `L7_ROUTE_VIOLATION` | OFI |
| route `COMPLIED_STOP`, verdict ∉ {Complied, InsufficientEvidence, ReviewRequired} | `L7_ROUTE_VIOLATION` | Complied |
| route `ROUTE_4_3` / `REVIEW_REQUIRED`, verdict ∉ {ReviewRequired, InsufficientEvidence} | `L7_ROUTE_VIOLATION` | ReviewRequired |
| route `L8` | none from L7 | — (G2–G7 apply) |

Rules that matter:
- The harness recomputes the route; a `route` the model writes is ignored.
- `ReviewRequired` is never an L7 violation (it is always the safe fallback).
- `COMPLIED_STOP` skips G6: a justified not-applicable means "requirement does not apply", not "implementation proven".
- Family B (`as appropriate`) is never closed by `not_applicable` (Annex A.2(a)).
- `condition_evidenced: true` overrides any determination (route L8).
- Several phrases on one element: an element with a family-B phrase is never closed by its family-A phrase.
- Combined routes: `ROUTE_4_3 > REVIEW_REQUIRED > L8 > OFI_STOP > COMPLIED_STOP`.

### Trace section

```json
"L7_conditional_qualifier": {
  "phrases": ["as applicable"],
  "condition_evidenced": false,
  "determination": "none | applicable | not_applicable | extent_determined",
  "justification": false,
  "a3_effect": "none | affects | unknown",
  "determination_conflict": false
}
```
`phrases`, `condition_evidenced` required. Defaults are fail-safe: `determination: none`, `justification: false`, `a3_effect: unknown`.

## 3. AWM behaviour

Opt-in evidence metadata (per `EvidenceItem.metadata`; absent = fail-safe):

| key | meaning |
|---|---|
| `org_determination` | `applicable` / `not_applicable` / `extent_determined` — the organization's own determination, recorded as evidence |
| `na_justification` | `true` when the claim was reasoned |
| `a3_effect` | `none` / `affects` / `unknown` (Annex A.3) |
| `condition_applies: false` | exclude an item from "activity evidence" |

- `GateTraceDeriver` adds `trace["L7_conditional_qualifier"]` and `derivation_provenance["l7_route"]`; verdict: OFI_STOP→OFI, COMPLIED_STOP→Complied (G6 skipped), ROUTE_4_3 / REVIEW_REQUIRED→ReviewRequired, L8 with state NOT_APPLICABLE→ReviewRequired.
- `AuditCognitionPipeline` passes `NOT_APPLICABLE` to the assessment **only** for non-family-B qualifier elements whose evidence records a not-applicable determination, with no activity evidence and no conflicting determinations. A qualifier element is therefore never mapped to `OUT_OF_SCOPE` merely because it is N/A (ref 71).
- `load_requirement_records()` (`scripts/requirement_profile_loader.py`) supplies corpus records, including `qualifier`, for `register_requirement()`.

## 4. Limits — read before relying on it

1. **Inputs are supplied, not inferred.** The gateway trusts what the model writes in the section (the harness catches contradictions with the verdict, not a false `determination`); AWM trusts opt-in metadata. Code that judges applicability from evidence (crosswalk gap #2) is still not built.
2. **Undetermined + no evidence** stays `INSUFFICIENT` in AWM and routes OFI / ReviewRequired, never NC.
3. **WG6 (pre-existing):** a snapshot where every requirement is N/A is not decision-ready (needs ≥ 1 APPLICABLE resolved requirement). A case whose only requirement is a justified not-applicable cannot reach a decision in AWM; the test suite documents this instead of hiding it.
4. WG0–WG5 in `WorldToDecisionAdapter.decide()` are still evaluated with all-default `True` flags (earlier-reported gap, unchanged).
5. The L7 slide image is not updated.
6. Event conditions ("when requirements are changed") are deliberately not triggers.

## 5. Verification

```
python -m pytest assets/tests/test_conditional_qualifiers.py assets/tests/test_controlled_retrieval.py assets/tests/test_l7_harness_gate.py -q
PYTHONPATH="scripts/awm_runtime;scripts" python -m pytest assets/tests/awm_v07/ -q
python scripts/run_regression_suite.py --skill-root . --outdir <scratch>
```
`test_l7_harness_gate.py` covers rejection/route/verdict matrix, malformed sections, the CLI path the gateway uses, and file-path loading by `ProductionHarnessAdapter`. `test_l7_awm.py` covers parity, `l7_inputs`, the deriver with the real harness, and end-to-end runs with corpus record AR-8.6-E02.
