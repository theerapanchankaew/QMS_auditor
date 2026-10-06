# Layered QMS Audit Cognition Engine — ISO 9001:2026 v1.0
> **Purpose:** Define the structured multi-layer reasoning architecture governing every material QMS audit evaluation.
> **Activation:** Required for routes: `conformity_evaluation`, `nc_classification`, `audit_workflow`, `full_ahp_evaluation`, `corrective_action_review`.
> **Design principle:** Evidence → Clause → Requirement Element → Conditional Gate → Breach Test → QMS Exposure → Severity Anchor → Counterfactual Challenge → Confidence/Escalation → F1 Calibration.

---

## Architecture Overview

```
[L1]  Controlled Source Boundary       (closed_source_entrypoint.py + controlled_source_guardrail.py)
       ↓
[L2]  Scope Gate                       (scope_gate.py → IN_SCOPE / OUT_OF_SCOPE)
       ↓
[L3]  Intent / Route Classifier        (route → reasoning mode)
       ↓
[L4]  Evidence Parser                  (extract objective evidence; separate from auditee claim)
       ↓
[L5]  Clause Mapper                    (evidence → correct ISO 9001:2026 clause using audit intent)
       ↓
[L6]  Requirement Element Decomposer   (clause → testable elements from ref 27)
       ↓
[L7]  Conditional Qualifier Gate       (family A applicability / B appropriateness / C extent)
       ↓
[L8]  Requirement Breach Test          (element + evidence + extent + effect)
       ↓
[L9]  QMS Exposure Analysis            (product/service conformity, customer/statutory/contract risk)
       ↓
[L10] NC Severity Calibrator           (M1–M5 = Major | D1–D4 = Minor; clause override from ref 25)
       ↓
[L11] Counterfactual Challenge         (challenge own verdict before finalizing)
       ↓
[L12] Confidence & Escalation Gate     (≥0.80 finalize | 0.60–0.79 ReviewRequired | <0.60 InsufficientEvidence)
       ↓
[L13] Human Auditor Output Frame       (ref 19-human-auditor-logic-prompt-contract.md)
       ↓
[L14] Benchmark / F1 Feedback Loop    (4-dimensional F1; ref 23-f1-score-governance.md)
```

---

## L1 — Controlled Source Boundary

**Pass condition:** `closed_source_entrypoint.py` returns `status: approved`.
**Fail behavior:** Show Thai boundary dialog. Stop immediately.
**Progress wording:** `Searching bundled QMS skill sources ...` — never "searching the web."

---

## L2 — Scope Gate

**IN_SCOPE:** ISO 9001 / QMS audit tasks → proceed to L3.
**OUT_OF_SCOPE:** Wrong standard (standalone ISO 14001, ISO 27001, etc.) or non-QMS task → return `OUT_OF_SCOPE`. Do NOT convert to ReferenceGap.
**AMBIGUOUS:** Ask one focused clarification question only.

---

## L3 — Intent / Route Classifier

| Route | When to use |
|---|---|
| `conformity_evaluation` | Full clause evaluation with evidence |
| `nc_classification` | Classify severity of a known finding |
| `corrective_action_review` | Assess CA adequacy, RCA quality, closure |
| `audit_workflow` | Checklist, plan, report generation |
| `iso_clause_advisor` | Clause interpretation, requirement explanation |
| `benchmark_evaluation` | Score PRED vs GT (ref guardrails/evaluation-benchmark-guardrail.md) |
| `evidence_gap_analysis` | Identify what evidence is missing |
| `full_ahp_evaluation` | AHP-weighted multi-clause risk scoring |

For `iso_clause_advisor`, layers L8–L11 are advisory only. For `conformity_evaluation` and `nc_classification`, all of L4–L11 are mandatory.

---

## L4 — Evidence Parser

**Mandate:** Populate the Evidence Object Schema (`references/28-evidence-schema.md` §1) before any verdict.

### Evidence Object Schema (required per case)

```json
{
  "case_id": "<identifier>",
  "clause": "<e.g. 8.6>",
  "auditee_claim": "<what the organization asserts>",
  "objective_evidence": ["<verifiable fact, record, observation, measurement>"],
  "missing_evidence": ["<what would confirm or deny but is absent>"],
  "evidence_strength": "strong | partial | weak | absent",
  "evidence_age": "current | stale | unknown",
  "implementation_proven": true | false,
  "record_proven": true | false,
  "effectiveness_proven": true | false | "not_required",
  "evidence_covers_all_material_elements": true | false,
  "evidence_sufficiency_status": "sufficient_for_minor_nc | insufficient_for_nc | review_required",
  "breach_proven": true | false,
  "sample_scope_verified": true | false,
  "evidence_gap_is_primary_issue": true | false,
  "conditional_qualifier_present": true | false,
  "applicability_outcome": "applies | not_applicable | not_assessed"
}
```

### QMS Evidence type weight table

| Type | QMS examples | Audit weight |
|---|---|---|
| Record | Inspection record, release record, supplier evaluation, calibration certificate | **Primary** |
| Sample | Sampled order, batch, project, customer complaint, NCR | **Primary** |
| Observation | Witnessed process step, physical product condition | **Primary** |
| Performance data | KPI trend, NCR trend, audit result, customer complaint trend | **High** |
| External/customer requirement | Contract, PO, customer spec, regulatory requirement | **High** |
| Interview (with corroborating record) | Interview trace + supporting document | **Medium** |
| Procedure / work instruction | Shows intent, not implementation | **Does NOT prove implementation** |
| Policy | Shows commitment, not conformance | **Very low** |
| Auditee verbal claim | Unrecorded assertion | **Not sufficient for Complied** |

**Critical rule:** Do NOT return `Complied` from a procedure or policy alone for implementation-heavy clauses (8.3, 8.4, 8.5, 8.6, 8.7, 9.2, 10.2). Verify `implementation_proven = true`.

**InsufficientEvidence ↔ Minor NC boundary rule:** If `evidence_gap_is_primary_issue = true`, `breach_proven = false`, or `sample_scope_verified = false`, do not return `Noncomplied/Minor`. Return `InsufficientEvidence` or `ReviewRequired` unless objective evidence independently proves a specific requirement breach.

---

## L5 — Clause Mapper

Map evidence to the correct ISO 9001:2026 clause using **audit intent**, not keyword matching.

| Evidence pattern | Primary clause | Audit intent signal |
|---|---|---|
| Risk and opportunity list / treatment | 6.1 | Were risks assessed? Actions integrated? |
| Product/service release record | 8.6 | Were acceptance criteria met and authorized? |
| Nonconforming product/service handling | 8.7 | Was disposition controlled and authorized? |
| Supplier approval record / evaluation | 8.4 | Was supplier evaluated before use? Critical supplier controlled? |
| Design/development record | 8.3 | Was D&D applicable? Was each phase controlled? |
| Internal audit record | 9.2 | Programme established? Risk areas covered? |
| Corrective action record | 10.2 | RCA conducted? CA effective? Recurrence? |
| Management review minutes | 9.3 | Required inputs present? Outputs actionable? |
| Calibration record / measurement equipment | 7.1.5 | Equipment used for release? Calibrated? |
| Competence / training record | 7.2 | Critical process covered? Effectiveness evaluated? |

**Intent-aware examples:**

```
"Release record signed but acceptance criteria field blank"
→ 8.6 — authorization traceable but criteria not proven → Major M3

"Supplier onboarded without evaluation but no quality issues found"
→ 8.4 — evaluation absent for critical supplier → Major M4 (risk: could become M1)

"Change implemented to production process without change review"
→ 6.3 + 8.5 — change not planned → Major M1/M3 if output affected
```

---

## L6 — Requirement Element Decomposer

Load the clause profile from `references/27-clause-requirement-profiles.md`. Check every requirement element independently.

```
For each requirement_element:
    Is there objective evidence covering this element?
    → YES: evidenced
    → PARTIAL: partial
    → NO: gap
    → Conditional qualifier: conditional_unevaluated

Coverage outcome:
    All material elements covered → Complied (no breach found)
    Core element absent            → breach test (L8)
    Entire process element absent  → Major trigger test (L9 Q4)
    Conditional element undetermined → L7 route (OFI for families A/C; family B proceeds to L8 and is InsufficientEvidence if unevidenced)
```

---

## L7 — Conditional Qualifier Gate (v2, 2026-10-06)

**Triggers (activate before L8):** a phrase from the canonical list below in the clause text of the element under test, or an element marked “by scope” / “by circumstance” in `references/27-clause-requirement-profiles.md`. The 22 clauses whose text carries a phrase are listed, with exact wording, in `references/standard/iso9001-2026-standard-map.md` (“Conditional qualifiers in clauses 4–10”). The vocabulary and the routing below are implemented in `scripts/conditional_qualifiers.py` (`PHRASE_FAMILY`, `l7_route`) and checked by `assets/tests/test_conditional_qualifiers.py`.

| Family | Canonical phrases | Meaning (Annex A.2 / A.3) |
|---|---|---|
| **A — applicability / relevance** | `as applicable` / `where applicable` / `when applicable` / `if applicable` / `if they are applicable` / `when relevant` (plus elements conditional by scope or circumstance) | the requirement can be determined not applicable in some situations — valid only under A.3 |
| **B — appropriateness** | `as appropriate` | the requirement applies; the organization judges what is suitable for its context. Not interchangeable with “applicable” |
| **C — extent / necessity** | `to the extent necessary` / `as necessary` / `if necessary` / `when it is necessary` | the organization determines the necessary extent (Annex A does not define these; the grouping is this project's) |

Equivalent constructions (“if / when / where / as” + applicable, relevant, appropriate or necessary) trigger the gate by their head word. Not triggers: adjectival uses (“applicable requirements”, “take appropriate action”) and event conditions (“when requirements are changed”). `if practicable` / `where practicable` / `as required by` were dropped from the earlier list: they do not occur in ISO 9001:2026 clauses 4–10. Elements conditional only by scope or circumstance (8.3 via 4.3, 8.5.3, 8.5.5, the 7.1.5.2 traceability lead-in) have no phrase and are handled as family A.

### Decision logic (MANDATORY before L8 for conditional elements)

```
Objective evidence that the condition applies (the circumstance/activity exists, or the
requirement is clearly needed) ALWAYS overrides a missing or contrary determination → L8.

FAMILY A  (applicability)
    no determination, no evidence it applies .......... OFI. STOP.   (not NC)
    organization says applicable ...................... → L8
    organization says NOT applicable:
        no justification .............................. OFI. STOP.   (not a valid determination:
                                                                      A.3 "considered … with justification", 4.3)
        justified AND no effect on conformity of products/services, customer
          satisfaction or statutory/regulatory obligations (A.3) → Complied. STOP.
        justified BUT it affects any of them (A.3 not met) ..... no Complied: judge the scope
                                                                  determination under 4.3 (AR-4.3-E07 / E09)
        justified, effect cannot be established from evidence .. ReviewRequired

FAMILY B  (appropriateness)
    never a not-applicable switch ..................... → L8
    L8 tests the organization's OWN justified, context-suitable approach; do not substitute your
    preferred one. No evidence → InsufficientEvidence (per L8): not NC, never Complied-by-N/A.
    A weak but reasonable approach → OFI/OBS, not NC.

FAMILY C  (extent / necessity)
    extent determined by the organization ............. → L8 against that extent
    not determined, no evidence of need ............... OFI. STOP.
    nil/limited extent, justified, no evidence of need  Complied. STOP.

STEP 2 — condition applies; requirement not implemented → classify Noncomplied per L10
```

Changes from v1: family B no longer routes “not applicable” to Complied (Annex A.2(a)); family A “not applicable → Complied” now needs the A.3 test, and “not applicable” without justification is OFI; the evidence-overrides rule is explicit on every path; one trigger vocabulary replaces the differing lists in SKILL.md / refs 08, 19, 26. Benchmark note: the answer key's label `L7_conditional_no_breach` is applied to any OFI-without-breach case, including clauses with no qualifier phrase — it is not an L7 qualifier test.

### QMS conditional clause table

| Clause | Qualifier in the text (family) | Default when unevaluated |
|---|---|---|
| 8.3 Design and development | none — conditional by scope (4.3 / Annex A.3) → A; 8.3.5 `as appropriate` (B), 8.3.6 `to the extent necessary` (C) | OFI if applicability not assessed; Major M4 if clearly applicable |
| 8.5.3 Property of external parties | none — by circumstance (only if such property exists) → A | OFI if no relevant property demonstrated |
| 8.5.4 Preservation | `to the extent necessary` (C) | OFI if no preservation-sensitive product demonstrated |
| 8.5.5 Post-delivery | none — by circumstance (post-delivery activities may not exist) → A | OFI if post-delivery obligations not demonstrated |
| 8.6 Release | `as applicable` (A) — customer approval; the acceptance criteria themselves are not qualified in the text | Must evaluate whether documented acceptance criteria needed |
| 7.1.5 Monitoring resources | 7.1.5.2: `as necessary` (C) under a “when traceability … is a requirement or is considered essential” lead-in (A, by circumstance) | OFI if not used for key measurements; Major M3 if used for release |

---

## L8 — Requirement Breach Test

### Four mandatory breach elements

```
Breach requires ALL FOUR:
  1. requirement_element  — which specific element of the clause was not met
  2. objective_evidence   — what concrete, verifiable evidence proves the gap
  3. extent               — isolated / partial / systemic / entirely absent
  4. effect               — actual or credible consequence (product risk, customer impact, regulatory breach)
```

If any missing:
- No evidence → `InsufficientEvidence`
- Possible concern not proven → `OBS`
- Process exists, improvement opportunity → `OFI`
- Partial evidence → `InsufficientEvidence` with evidence gap statement

### Gate 1A handoff — evidence gap versus Minor NC

Before L9/L10 severity classification, test whether the candidate Minor NC is actually an evidence-sufficiency problem:

```text
IF proposed verdict = Noncomplied/Minor AND
   (breach_proven = false OR evidence_gap_is_primary_issue = true OR sample_scope_verified = false):
      verdict = InsufficientEvidence or ReviewRequired
      nc_class = null
      trigger_or_anchor = insufficient_evidence
      STOP before severity calibration
```

A missing or limited sample supports Minor NC only when the applicable requirement requires the retained evidence and the absence/incompleteness is objectively verified. Otherwise, missing evidence remains an evidence gap, not a nonconformity.

---

## L9 — QMS Exposure & Conformity Risk Analysis

Run Q1–Q5 for every Noncomplied candidate. Name the M-trigger if found.

```
Q1: Does the control failure directly expose product/service conformity?
    (Nonconforming output risk, uncontrolled production, release before verification)
    YES → Major trigger M1

Q2: Is there an actual or imminent breach of a customer, statutory, regulatory, or contract requirement?
    YES → Major trigger M2

Q3: Was product/service released or delivered without required verification, 
    or was nonconforming output released without authorization?
    YES → Major trigger M3

Q4: Is an entire required QMS system element completely absent?
    (No CA process, no internal audit programme, no design control when applicable, 
    no supplier evaluation for any supplier)
    YES → Major trigger M4

Q5: Has the same NC recurred after a verified corrective action closure?
    Or is failure widespread across multiple sites/processes?
    YES → Major trigger M5

Q6: None of Q1–Q5 triggered:
    → classify as Minor D1–D4 per calibration table (ref 25)
```

---

## L10 — NC Severity Calibrator

### Hard rule: Every Noncomplied verdict MUST include

```json
{
  "verdict": "Noncomplied",
  "nc_class": "Major | Minor",
  "trigger_or_anchor": "M1 | M2 | M3 | M4 | M5 | D1 | D2 | D3 | D4",
  "decisive_question_answered": "<single question that controlled the severity decision>"
}
```

**Major:** Named M-trigger proven by objective evidence. If no M-trigger → downgrade to Minor or ReviewRequired.

**Minor:** D-anchor required:
- D1: Record/documentation gap, no conformity exposure
- D2: Process weak or incomplete (not absent)
- D3: Behavioral/awareness gap without demonstrated system failure
- D4: Isolated single lapse without pattern or recurrence

### Severity override check (after Q1–Q5)

Cross-check severity against `references/25-nc-severity-calibration-guide.md` clause table. If table suggests different severity than L9 → use the more conservative (higher) classification or escalate to `ReviewRequired`.

---

## L11 — Counterfactual Challenge

### Before finalizing MAJOR

```
1. Which M-trigger (M1–M5) is proven by objective evidence? Name it.
2. Is this merely a documentation or process weakness with no product/service conformity risk?
3. Would a competent QMS auditor accept Minor if the exposure is only hypothetical?

CANNOT NAME an M-trigger → downgrade to Minor or ReviewRequired.
```

### Before finalizing MINOR

```
1. Is there actual or imminent breach of a customer/statutory/regulatory/contract requirement? → M2
2. Was product/service released before required verification? → M3
3. Is an entire required system element absent? → M4
4. Has the same NC recurred after a verified CA? → M5

YES to any → re-enter L9 and re-evaluate Major triggers.
```

### Before finalizing OFI

```
1. Does the clause have a conditional qualifier? → OFI valid if the condition is undetermined (family A/C); family B is never an OFI-by-not-applicable
2. Does objective evidence show the condition actually applies? → proceed to breach test
3. Has a pattern or recurrence been shown? → reconsider Minor/Major
```

### Before finalizing Complied

```
1. Does evidence cover ALL material requirement elements (not just policy)?
2. Is implementation_proven = true for implementation-heavy clauses?
3. Is evidence current (not stale since last significant change)?
4. If effectiveness required by clause: is effectiveness_proven = true?

ANY NO → reconsider InsufficientEvidence or OFI
```

---

## L12 — Confidence & Escalation Gate

| Confidence | State | Action |
|---|---|---|
| 0.90–1.00 | Strong direct current evidence, all elements covered | Finalize |
| 0.80–0.89 | Adequate with minor limitations | Finalize with caveat |
| 0.60–0.79 | Partial evidence or interpretation gap | `ReviewRequired` |
| < 0.60 | Insufficient or conflicting evidence | `InsufficientEvidence` or `ReviewRequired` |

If Major verdict but no M-trigger can be named → confidence cannot exceed 0.79 → `ReviewRequired`.

---

## L13 — Human Auditor Output Frame

Apply `references/19-human-auditor-logic-prompt-contract.md`.

**Required output fields for every material verdict:**

```
1. Human Auditor Frame — mode, source boundary, external sources confirmation
2. Audit Objective — what is being evaluated
3. Controlled Sources Used — reference trace
4. Evidence Object — structured per L4 schema
5. Requirement Element Coverage — per L6 analysis
6. Conditional Qualifier Result — L7 outcome (if applicable)
7. Breach Confirmation — L8 result
8. Exposure Analysis — L9 Q1–Q5 summary
9. Verdict + nc_class + trigger_or_anchor + decisive_question_answered
10. Confidence level
11. Evidence gaps and next audit questions (≤3)
12. Counterfactual challenge summary
```

**Allowed verdicts (complete list):**
`Complied` | `Noncomplied` | `OFI` | `OBS` | `InsufficientEvidence` | `ReviewRequired` | `ReferenceGap` | **`OUT_OF_SCOPE`** | `Informational`

---

## L14 — Benchmark / F1 Feedback Loop

Track 4-dimensional F1 — Binary alone is insufficient.

| Dimension | Measures | Min threshold |
|---|---|---|
| **Binary F1** | Issue vs no-issue | ≥0.90 |
| **Verdict F1** | Exact verdict match | ≥0.75 |
| **NC Class F1** | Major vs Minor accuracy | ≥0.70 |
| **Clause-specific F1** | Per clause group | ≥0.70 per clause |

For benchmark evaluation: `references/guardrails/evaluation-benchmark-guardrail.md` (P0).

---

## Structured Reasoning Contract (use in system prompt / task framing)

```
You are a QMS human-auditor reasoning engine operating in closed-source mode.
Standard: ISO 9001:2026. Source boundary: bundled QMS skill bundle only.

For each case, execute the Layered QMS Audit Cognition Engine in layer order:

L4: Parse evidence → separate auditee_claim from objective_evidence.
    Populate Evidence Object (references/28-evidence-schema.md §1).
    Set: implementation_proven, record_proven, evidence_strength, evidence_age.

L5: Map evidence to correct ISO 9001:2026 clause using audit intent, not keyword matching.

L6: Load clause profile (references/27-clause-requirement-profiles.md).
    Check each requirement element: evidenced | gap | partial | conditional_unevaluated.

L7: Check conditional qualifiers (families A/B/C, see § L7). Family A/C undetermined and no evidence the
    condition applies → verdict = OFI. STOP. Do not proceed to L8. Family B → L8.

L8: Confirm breach with all four: requirement_element + objective_evidence + extent + effect.
    Missing any → InsufficientEvidence or OBS, not NC.

L9: Run Q1–Q5 QMS exposure analysis. Name M-trigger or confirm Q6 (no major trigger).

L10: Assign nc_class + trigger_or_anchor + decisive_question_answered.
     Major requires named proven M-trigger. No M-trigger → Minor or ReviewRequired.

L11: Counterfactual challenge before finalizing any verdict.
     Major: name M-trigger. Minor: confirm no Q1–Q5 = YES.

L12: Confidence ≥0.80 → finalize. 0.60–0.79 → ReviewRequired. <0.60 → InsufficientEvidence.

Output required fields per case:
  case_id, clause, verdict, nc_class, trigger_or_anchor,
  decisive_question_answered, confidence, evidence_gaps

Prohibited:
  - Do not use external knowledge, web sources, or base training memory.
  - Do not return Major without a named M-trigger.
  - Do not return NC for a conditional clause without running L7.
  - Do not return Complied from policy/procedure alone for implementation-heavy clauses.
  - Do not return OUT_OF_SCOPE from ReviewRequired for wrong-standard requests.
```
