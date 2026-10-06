# Evidence Schema & Decision Trace — QMS Auditor v1.0
> **Purpose:** Canonical data schemas for evidence parsing (L4) and audit decision tracing (L10–L12).
> **Usage:** Populate schemas before any verdict decision. REQUIRED fields must be present.
> **Related:** `references/26-layered-audit-cognition.md` L4; `references/06-evidence-dictionary.md`

---

## 1. Evidence Object Schema

Populate at **L4 (Evidence Parser)** before any clause mapping or verdict decision.

```json
{
  "case_id": "QMS-TC-XXX-XX",
  "clause": "X.X.X",
  "audit_type": "document_review | record_sampling | interview | observation | performance_data_review",

  "auditee_claim": "<what the organization asserts — unverified until corroborated>",

  "objective_evidence": [
    "<item 1: verifiable fact from record, observation, or measurement>",
    "<item 2: ...>"
  ],

  "missing_evidence": [
    "<what would be needed to confirm but is absent>",
    "<e.g. 'release authorization record not presented', 'calibration certificate not available'>"
  ],

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
  "conditional_qualifier_text": "<qualifier from clause if present>",
  "applicability_assessed": true | false | "unknown",
  "applicability_outcome": "applies | not_applicable | not_assessed"
}
```

### Evidence weight table (QMS-specific)

| Evidence type | QMS examples | Verdict weight |
|---|---|---|
| Release record | Signed inspection/test record, acceptance authorization | **Primary — required for 8.6** |
| NC record | Nonconformance report, disposition record | **Primary — required for 8.7** |
| Supplier evaluation | Approved supplier record, audit result, evaluation form | **Primary — required for 8.4** |
| Design record | Design review minutes, verification/validation record | **Primary — required for 8.3** |
| Calibration certificate | Traceable calibration record | **Primary for 7.1.5** |
| CA record | RCA, CA plan, effectiveness verification | **Primary — required for 10.2** |
| Internal audit record | Audit report, programme, schedule | **Primary — required for 9.2** |
| Performance data | KPI, NCR trend, customer complaint trend, satisfaction data | **High** |
| Sample from operation | Sampled order, batch, project, complaint | **High** |
| Interview (with record) | Interview trace + supporting document | **Medium** |
| Procedure / work instruction | Defines process intent | **Does NOT prove implementation** |
| Policy | Commitment statement | **Very low — not sufficient for implementation clauses** |
| Verbal claim | Unrecorded auditor assertion | **Not sufficient for Complied** |

**Hard rule:** `Complied` requires `implementation_proven = true` for clauses 8.3, 8.4, 8.5, 8.6, 8.7, 9.2, 10.2.

**IE ↔ Minor boundary rule:** `Noncomplied/Minor` requires `breach_proven = true`, `evidence_gap_is_primary_issue = false`, and sufficient extent/sample scope to support a requirement breach. If evidence is partial, indirect, or limited such that the auditor cannot prove breach, use `InsufficientEvidence` or `ReviewRequired`, not Minor NC.

---

## 2. Clause Element Coverage Map

Populate at **L6 (Requirement Element Decomposer)** after loading clause profile from `references/27-clause-requirement-profiles.md`.

```json
{
  "case_id": "QMS-TC-XXX-XX",
  "clause": "8.6",
  "requirement_elements_checked": [
    {
      "element_id": "8.6-E1",
      "element_description": "Planned arrangements for release completed",
      "evidence_status": "evidenced | gap | partial | conditional_unevaluated | not_applicable",
      "evidence_note": "<brief description>"
    },
    {
      "element_id": "8.6-E2",
      "element_description": "Acceptance criteria met with objective evidence",
      "evidence_status": "gap",
      "evidence_note": "Inspection record present but acceptance criteria field blank"
    },
    {
      "element_id": "8.6-E3",
      "element_description": "Release authorization traceable to authorized person",
      "evidence_status": "partial",
      "evidence_note": "Signature present but authorization scope not documented"
    }
  ],
  "material_elements_with_gaps": ["8.6-E2"],
  "all_material_elements_covered": false
}
```

**Evidence status codes:**

| Code | Meaning |
|---|---|
| `evidenced` | Objective evidence directly covers this element |
| `partial` | Some evidence but incomplete coverage |
| `gap` | Required but no evidence found |
| `conditional_unevaluated` | Family A/C qualifier (ref 26 § L7); condition undetermined and no evidence it applies → OFI. Family B never uses this state (it proceeds to L8) |
| `not_applicable` | Organization determined element not applicable with justification |

---

## 3. Decision Trace Schema

Populate at **L10–L12**. Required for all `Noncomplied` verdicts.

```json
{
  "case_id": "QMS-TC-XXX-XX",
  "route": "nc_classification | conformity_evaluation | ...",
  "clause": "X.X.X",
  "cognition_layers_executed": ["L4","L5","L6","L7","L8","L9","L10","L11","L12"],

  "l7_conditional_qualifier_result": "not_applicable | OFI | applies_proceed_to_L8",
  "l8_breach_confirmed": true | false,
  "l8_breach_elements": {
    "requirement_element": "<which specific element failed>",
    "objective_evidence": "<what proves the breach>",
    "extent": "isolated | partial | systemic | entirely_absent",
    "effect": "<actual or credible consequence>"
  },

  "l9_exposure_analysis": {
    "Q1_product_conformity_exposed": false,
    "Q2_customer_statutory_contract_breach": false,
    "Q3_release_without_verification": false,
    "Q4_system_element_absent": true,
    "Q5_recurrence_or_systemic": false,
    "Q6_no_major_trigger": false,
    "major_trigger_identified": "M4 | none"
  },

  "l10_severity": {
    "nc_class": "Major | Minor",
    "trigger_or_anchor": "M4 | D2 | ...",
    "decisive_question_answered": "<the single question that controlled the severity decision>"
  },

  "l11_counterfactual": {
    "major_challenge_passed": true | false | "not_major",
    "major_challenge_notes": "<if Major: M-trigger named and why it holds>",
    "minor_challenge_passed": true | false | "not_minor",
    "minor_challenge_notes": "<if Minor: confirmed no Major triggers apply>"
  },

  "l12_confidence": 0.88,
  "l12_escalation": "none | ReviewRequired | InsufficientEvidence",

  "ie_minor_boundary": {
    "evidence_sufficiency_status": "sufficient_for_minor_nc | insufficient_for_nc | review_required",
    "breach_proven": true | false,
    "sample_scope_verified": true | false,
    "evidence_gap_is_primary_issue": true | false,
    "gate_result": "minor_confirmed | converted_to_insufficient_evidence | review_required",
    "reason": "<brief reason>"
  },

  "verdict": "Noncomplied",
  "nc_class": "Major | Minor | null",
  "trigger_or_anchor": "M4",
  "decisive_question_answered": "Is an entire required QMS system element completely absent?",
  "confidence": 0.88,
  "evidence_gaps": ["<list of what is missing>"],
  "next_audit_questions": ["<up to 3 focused follow-up questions>"]
}
```

---

## 4. 4-Dimensional Calibration Memory

Record per case for L14 (F1 Feedback Loop). Enables clause-specific upskill targeting.

```json
{
  "case_id": "QMS-TC-XXX-XX",
  "clause_group": "8.6",
  "route": "conformity_evaluation",

  "binary_verdict": "issue | no_issue",
  "full_verdict": "Complied | Noncomplied | OFI | OBS | InsufficientEvidence",
  "nc_class_predicted": "Major | Minor | null",

  "binary_correct": true | false,
  "verdict_correct": true | false,
  "nc_class_correct": true | false | "not_applicable",

  "failure_type": "FP | FN | verdict_mismatch | nc_class_mismatch | correct",
  "failure_layer": "L7_conditional_qualifier | L8_breach | L9_exposure | L10_severity | L11_counterfactual | L4_evidence | L5_clause | none",
  "notes": "<pattern description>"
}
```

**Failure layer attribution:**

| Error pattern | Likely layer | Upskill action |
|---|---|---|
| OFI vs Noncomplied | **L7** — conditional qualifier gate missed | Enforce L7 before L8 |
| Major vs Minor mismatch | **L9** + **L10** + **L11** | Add exposure Q1–Q5 + clause override |
| Wrong clause | **L5** — intent mapping missed | Load clause mapper audit intent table |
| Complied vs InsufficientEvidence | **L4** — claim vs evidence separation | Enforce `implementation_proven` check |
| Complied vs OFI | **L6** + **L11** — element gap not detected | Load clause requirement profile |

---

## 5. QMS Context Schema (batch evaluation)

```json
{
  "organization_context": {
    "sector": "<manufacturing | services | construction | software | healthcare | other>",
    "size": "small | medium | large",
    "scope": "<products/services in scope of QMS>",
    "applicable_clauses": ["8.3", "8.4", "8.5", "8.6", "8.7"],
    "known_major_ncs": ["<prior Major NCs from previous audit if evidenced>"],
    "known_customer_complaints": ["<significant complaints if evidenced>"],
    "previous_ca_closure": ["<CA IDs closed as effective — triggers M5 check if recurrence found>"],
    "certification_stage": "initial | surveillance | recertification"
  }
}
```

Presence of `known_major_ncs` or `previous_ca_closure` triggers automatic L9-Q5 (recurrence) check for related clauses.

---

## 6. Benchmark Evaluation Schema

For use with `scripts/benchmark_evaluator.py` and `references/guardrails/evaluation-benchmark-guardrail.md`.

```json
{
  "case_id": "QMS-TC-XXX-XX",
  "gt_source": "answer_key.jsonl",
  "gt_verdict": "<from JSONL field: verdict>",
  "gt_nc_class": "<from JSONL field: nc_class — normalize None/N/A/blank to null>",
  "pred_source": "generated_report.md or .jsonl",
  "pred_verdict": "<from report field: generated_verdict>",
  "pred_nc_class": "<from report field: generated_nc_class>",
  "verdict_match": true | false,
  "nc_class_match": true | false | "not_applicable",
  "failure_type": "FP | FN | nc_class_mismatch | correct"
}
```

**Source role contract (never swap):**
- `answer_key.jsonl` → Ground Truth fields: `verdict`, `nc_class`
- Generated report → Prediction fields: `generated_verdict`, `generated_nc_class`
