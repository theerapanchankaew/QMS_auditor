# Major Escalation Gate — v2.0
> **Upskill module ID:** `qms-major-escalation-gate-v2`
> **Type:** `clause_guide_module`
> **Version:** 2.0.0
> **Replaces:** L9/L10 sections in `references/26-layered-audit-cognition.md`
> **Benchmark evidence:** Major Recall = 0.5333 (16/30) — 14 Major cases downgraded to Minor
> **Root cause:** L9 Q1–Q5 check was bypassed when evidence pattern was "absent + mismatch" but risk level was judged ambiguous; model defaulted to Minor D2 instead of seeking M-trigger
> **Fix:** Three hard enforcement rules below + mandatory pre-downgrade challenge

---

## Purpose

This module strengthens the Major trigger detection path (L9–L11) to eliminate under-escalation bias. The benchmark showed that Major precision was high (0.941) but recall was critically low (0.533), meaning the model correctly identified Major *when it committed*, but was too conservative in committing. This module adds three mandatory gates that must execute before any downgrade from Major candidate → Minor.

---

## Rule 1 — Mandatory Q1–Q5 Exhaustion Before Minor

**Hard rule (overrides L10 default):**

Before classifying any `Noncomplied` as `Minor`, the model MUST have explicitly evaluated all five Major exposure questions Q1–Q5. A Minor verdict is only valid when Q6 is confirmed — i.e., ALL of Q1–Q5 return NO.

```
MANDATORY PRE-MINOR CHECKLIST (execute at L9, document result):

Q1 — Does control failure directly expose product/service conformity to risk?
     Evidence signal: uncontrolled production step, missing inspection record,
     supplier not evaluated for product-affecting inputs, calibration lapsed for
     release-critical equipment.
     → YES → Major M1. STOP. Do not proceed to Minor.

Q2 — Is there actual or imminent breach of customer/statutory/regulatory/contract?
     Evidence signal: PO term unmet, regulatory threshold exceeded, contract
     deviation evidenced, mandatory external communication not done.
     → YES → Major M2. STOP.

Q3 — Was product/service released or delivered without required verification?
     Or was nonconforming output released without authorization?
     Evidence signal: shipment record precedes acceptance record, 8.6 field blank,
     concession issued without authorization, 8.7 disposition unrecorded for
     released output.
     → YES → Major M3. STOP.

Q4 — Is an entire required QMS system element completely absent?
     Evidence signal: NO process at all (not weak — absent) for:
     internal audit | CA process | supplier evaluation (any) | design control
     (when applicable) | release criteria | risk/opportunity planning.
     → YES → Major M4. STOP.

Q5 — Has the same NC recurred after a verified CA closure?
     Or is failure widespread across multiple sites/processes?
     Evidence signal: same clause NC in prior audit cycle, multi-site sampling
     shows same gap, CA effectiveness record absent at re-audit.
     → YES → Major M5. STOP.

Q6 — All Q1–Q5 = NO → Minor D1–D4 permitted. Document: "Q6 confirmed."
```

**Failure mode this prevents:** Model sees "ไม่มี/ไม่ครบ + ผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก" and classifies Minor D2 without checking whether the missing element is an entire system element (Q4) or affects product conformity (Q1).

---

## Rule 2 — High-Risk Clause × Evidence-Absent = Presumptive Major Check

When ALL THREE conditions are present simultaneously, a Major trigger check is **presumed necessary** and the model must explicitly confirm or deny each M-trigger before Minor is permitted:

| Condition A | Condition B | Condition C |
|---|---|---|
| `completely_absent = true` (ไม่มี/ไม่ครบ + ไม่พบหลักฐาน) | `risk_sensitivity ∈ {high, high-sensitive, very high}` | `clause ∈ high_risk_set` |

**High-risk clause set for this rule:**
```
8.1, 8.2.2, 8.2.3.1, 8.2.3.2, 8.2.4,
8.3.2, 8.3.3, 8.3.4, 8.3.5, 8.3.6,
8.4.1, 8.4.2, 8.4.3,
8.5.1, 8.5.2, 8.5.3, 8.5.4, 8.5.5, 8.5.6,
8.6, 8.7.1, 8.7.2,
9.1.1, 9.1.2, 9.2.1, 10.2.1
```

**Trigger:** When all three conditions are met → run Q1–Q5 exhaustively → document result → only then may Minor be returned if Q6 confirmed.

**Failure mode this prevents:** Model classifies 7.2 (Competence) as Minor D2 even when the competence gap directly exposes a quality-critical process to unqualified operator (→ should be M1).

---

## Rule 3 — Statement-Mismatch Escalation Signal

When evidence includes `ผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก` (interview contradicts records) AND the clause is in the high-risk set:

```
IF interview_contradicts_records = true
AND clause ∈ high_risk_set
AND completely_absent = true:
    → confidence ceiling = 0.79 (cannot finalize without ReviewRequired or Major)
    → Q1–Q5 mandatory before any verdict
    → If any Q returns YES → Major
    → If all Q = NO but contradiction unresolved → ReviewRequired (not Minor)
```

**Rationale:** Interview contradiction + missing records in a high-risk clause is not a D1/D2 pattern — it signals potential intentional concealment or systemic control breakdown. The model should not "helpfully" resolve this ambiguity toward Minor.

---

## Calibration Table Addendum — Clauses Where Benchmark Failed

These clauses showed Major→Minor downgrade in the benchmark. Severity override rules apply:

| Clause | GT | Pred | Rule |
|---|---|---|---|
| 7.2 | Major | Minor | Competence gap for quality-critical process → Q1 check mandatory: if process output has conformity risk → M1 |
| 9.1.1 | Major | Minor | Monitoring absent for key processes → Q4 if entire process absent; Q1 if release-affecting |
| 9.3.1 | Major | Minor | No management review → Q4 (entire element absent) = M4 by table |
| 7.5.2 | Major | Minor | Document control gap for critical parameter → Q1 if undocumented critical step |
| 8.3.2 | Major | Minor | Design planning absent → Q4 (design element absent when applicable) = M4; Q3 if unverified design released |
| 4.4.2 | Major | Minor | QMS documented information element absent → Q4 |
| 6.1.1 | Major | Minor | Risk planning absent → Q4; Q1 if risk materialized |
| 9.2.2 | Major | Minor | Internal audit findings not followed up → Q5 (recurrence after CA) |
| 8.2.4 | Major | Minor | Changes to requirements without review → Q1/Q3 |
| 10.2.2 | Minor | Major | Overcall — D2 correct if process exists but weak without recurrence |

---

## SKILL.md Integration — Add to "★ Layered QMS Audit Cognition Engine" section

Add after the existing "Cognition engine hard rules" block:

```markdown
**Rule added by upskill module `qms-major-escalation-gate-v2`:**

6. **Pre-Minor Gate** — Before finalizing any Minor verdict, confirm Q6 (all Q1–Q5 = NO) explicitly. If any Q was not evaluated, evaluate it now. Document result in `decisive_question_answered`.

7. **High-risk clause presumption** — When `completely_absent = true` AND `risk_sensitivity ∈ {high, high-sensitive, very high}` AND `clause ∈ high_risk_set` (see ref 36): presume Major candidate; run all Q1–Q5 exhaustively before Minor is permitted.

8. **Statement-mismatch ceiling** — When interview contradicts records AND clause is high-risk AND evidence absent: confidence ceiling = 0.79 → ReviewRequired minimum unless Q1–Q5 explicitly confirms Q6.
```

---

## F1 Impact Projection

| Metric | Before (v5.1) | Target after (v5.2) |
|---|---|---|
| Major Recall | 0.5333 | ≥ 0.88 |
| Major F1 | ~0.69 | ≥ 0.87 |
| Minor F1 | 0.908 | ≥ 0.90 (monitor for overcall) |
| NC Class Macro F1 | 0.861 | ≥ 0.88 |
