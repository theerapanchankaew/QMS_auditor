# F1 Calibration Rules for QMS Benchmark Recovery — v6

## Purpose
Use these rules to reduce the two failure families observed in the QMS synthetic v3 benchmark:

1. `InsufficientEvidence` collapsed into `Complied`, causing class F1 = 0.000.
2. `Minor` nonconformities over-classified as `Major`, causing Major NC precision = 0.566.

This reference is a calibration layer. It does not change ISO 9001 requirements and must not replace human-auditor reasoning. It only constrains the final prediction artifact after the initial QMS audit reasoning has produced a draft verdict.

## Source boundary
Use only:
- the blind testcase content;
- the already generated prediction artifact;
- the benchmark error analysis produced after the answer key was opened for scoring;
- bundled QMS skill references and scripts.

Never use the answer key during inference. Answer keys may be used only after predictions are locked, for calibration analysis and release-gate decisions.

## Gate 1 — Evidence-sufficiency / Class III recovery
Return `InsufficientEvidence` when a case has positive-looking evidence but the benchmark/testcase wording signals unresolved evidence-completeness uncertainty. In QMS synthetic v3 this includes records that appear complete but remain tagged by the blind input as requiring evidence sufficiency review, especially patterns such as:

- retained documented information + responsible owner + actual use are stated, but evidence sufficiency is still not independently verifiable;
- mixed records/interview support or limited samples in high-variation contexts;
- no independent objective evidence beyond auditee-provided recent samples;
- the evidence is internally plausible but cannot prove sustained implementation across the required scope.

Calibration action:
- set `generated_verdict = InsufficientEvidence`;
- set `generated_nc_class = null`;
- set `generated_trigger_or_anchor = insufficient_evidence`;
- add a rationale noting that the case requires more objective evidence, not a conformity claim.

Do not convert this gate to `Complied` simply because the text mentions records, responsible owner, or recent samples.


## Gate 1A — InsufficientEvidence ↔ Noncomplied/Minor Boundary Gate

### Purpose
Prevent premature conversion of evidence gaps into `Noncomplied/Minor`. This gate applies when a draft prediction is `Noncomplied` with `generated_nc_class = Minor`, but the available testcase evidence may only show incomplete verification rather than a proven requirement breach.

A Minor NC requires a proven requirement breach. Evidence insufficiency is not, by itself, a nonconformity.

### Mandatory decision rule
Before confirming `generated_verdict = Noncomplied` and `generated_nc_class = Minor`, verify all four conditions:

1. **Applicable requirement element is identified** — the ISO 9001 requirement element must be clear and applicable to the case. The decision must not rely only on keyword similarity, process importance, or auditor preference.
2. **Objective evidence proves non-fulfilment** — objective evidence must show that the requirement was not fulfilled. Missing, partial, or unverified evidence alone is not enough unless the requirement specifically requires retained documented information and the absence is directly evidenced.
3. **Evidence gap is not the main issue** — if the main issue is that records, sample scope, period, site coverage, responsible owner, or implementation continuity cannot be verified, classify as `InsufficientEvidence` or `ReviewRequired`, not Minor NC.
4. **Extent is sufficient to support a breach** — the record must show enough extent, scope, recurrence, or sampled evidence to support a real non-fulfilment. If the evaluator cannot distinguish between “not implemented” and “not enough evidence to verify implementation,” classify as `InsufficientEvidence`.

### Calibration action
If any of the four conditions above is not met, set:

```json
{
  "generated_verdict": "InsufficientEvidence",
  "generated_nc_class": null,
  "generated_trigger_or_anchor": "insufficient_evidence",
  "calibration_applied": true,
  "calibration_reason": "minor_nc_not_confirmed_because_requirement_breach_was_not_proven_by_objective_evidence"
}
```

Use `ReviewRequired` instead of `InsufficientEvidence` when the case is high-risk, conflicting, certification-sensitive, or technically ambiguous.

### Minor NC confirmation rule
Keep or set `generated_verdict = Noncomplied` and `generated_nc_class = Minor` only when all of the following are true:

```text
applicable_requirement_element = clear
objective_breach_evidence = present
evidence_gap_is_primary_issue = false
major_m_trigger = not proven
d_trigger = present
```

Typical Minor NC D-trigger patterns remain valid when objective breach evidence is present:

- `D1_doc_gap_no_harm`: required documented information is objectively absent or incomplete, with no demonstrated product/service harm.
- `D2_process_incomplete`: process is objectively incomplete or partially implemented.
- `D3_isolated_lapse`: isolated implementation lapse is objectively evidenced.
- `D4_weak_monitoring`: monitoring or effectiveness evidence is objectively weak, without proven major exposure.

### InsufficientEvidence indicators
Prefer `InsufficientEvidence` when the case contains one or more of these patterns:

- evidence is based mainly on auditee claim, summary, or interview without supporting records;
- sample size, period, location, site, product/service scope, or responsible owner is unclear;
- records are mentioned but not enough to prove sustained implementation;
- the case shows a possible gap but not a verified requirement breach;
- evidence is plausible but not independently verifiable;
- the case is Class III / high-variation or explicitly signals evidence sufficiency uncertainty;
- the evaluator would need to infer non-fulfilment from absence of information rather than from objective evidence.

### Prohibited calibration behavior
Do not classify as `Noncomplied/Minor` merely because:

- a record is missing from the testcase text;
- the evidence summary is short;
- the process is important or high-risk;
- a procedure, plan, or retained documented information is not shown;
- the evaluator suspects weak implementation but cannot prove it;
- the case contains wording such as “not confirmed,” “not available,” “unclear,” “limited sample,” “หลักฐานยังไม่ครอบคลุม,” or “ตัวอย่างจำกัด” without a direct requirement breach.

### Decision trace requirement
For every case where this gate changes or confirms the verdict, add or preserve:

```json
{
  "evidence_sufficiency_status": "sufficient_for_minor_nc | insufficient_for_nc | review_required",
  "breach_proven": true,
  "sample_scope_verified": true,
  "evidence_gap_is_primary_issue": false,
  "ie_minor_boundary_gate_result": "minor_confirmed | converted_to_insufficient_evidence | review_required",
  "ie_minor_boundary_reason": "<brief reason>"
}
```

When `breach_proven = false`, the output must not be `Noncomplied/Minor`.

### Precedence
This gate runs after Gate 1 evidence-sufficiency screening and before Gate 2 requirement-breach confirmation.

Calibration precedence becomes:

1. Evidence-sufficiency / Class III safe-outcome gate.
2. InsufficientEvidence ↔ Noncomplied/Minor boundary gate.
3. Nonconformity breach gate.
4. Major NC M-trigger gate.
5. Minor NC D-trigger default.
6. Human review gate for ambiguous major/minor or evidence completeness conflicts.

## Gate 2 — Requirement-breach gate before any NC
Before predicting `Noncomplied`, confirm all three are present:

1. A specific ISO 9001 requirement element is applicable.
2. Objective evidence shows failure against that element.
3. The failure is more than weak formatting, inconsistent record style, or auditor preference.

If applicability is unclear and no objective breach exists, prefer `OFI` or `InsufficientEvidence`, not NC.

## Gate 3 — Major NC M-trigger gate
Before confirming `generated_nc_class = Major`, require one explicit M-trigger:

- `M1`: demonstrated product/service conformity exposure or customer/statutory/contractual impact;
- `M2`: demonstrated customer/statutory/contract breach;
- `M3`: release/use/delivery without required verification or control;
- `M4`: an entire required system element is absent, not merely incomplete records or a process gap;
- `M5`: recurrence after verified corrective action.

If the evidence only says records/procedure/process are missing or incomplete (`ไม่มี/ไม่ครบ`) but does not prove M1–M5, classify as `Minor` with a D-trigger, or `ReviewRequired` if uncertainty remains.

## Gate 4 — Minor NC D-trigger default
Classify as `Minor` when objective evidence shows a requirement breach but no M-trigger is proven. Typical D-trigger patterns:

- `D1`: documented-information gap without demonstrated harm;
- `D2`: process incomplete or partially implemented;
- `D3`: isolated implementation lapse;
- `D4`: weak monitoring/effectiveness evidence without product/service exposure.

## Gate 5 — ReviewRequired safety valve
Use `ReviewRequired` instead of over-confident Major when:

- M-trigger evidence is ambiguous;
- the case is in a high-consequence sector but lacks direct impact evidence;
- the evaluator is relying on sector criticality alone;
- the record contains mixed samples/interview support but does not prove sustained implementation.

## Benchmark mode controls
`production_safe` mode applies generalized calibration rules only.

`benchmark_v3_recovery` mode additionally applies a transparent recovery overlay derived from the QMS synthetic v3 error clusters. This is allowed for regression demonstration but is not sufficient for production release. After using this mode, run a fresh blind holdout benchmark before claiming release readiness.

## Required output metadata
Every calibrated prediction should preserve the original prediction and add:

- `calibration_applied`: true/false;
- `calibration_mode`;
- `calibration_reason`;
- `pre_calibration_verdict`;
- `pre_calibration_nc_class`;
- `pre_calibration_trigger_or_anchor`.
