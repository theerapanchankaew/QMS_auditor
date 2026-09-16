# InsufficientEvidence Hard Gate — v1.0
> **Upskill module ID:** `qms-insufficient-evidence-gate-v1`
> **Type:** `clause_guide_module`
> **Version:** 1.0.0
> **Benchmark evidence:** InsufficientEvidence Recall = 0.000 (0/21) — all 21 cases predicted as Complied (20) or NC (1)
> **Root cause:** L12 Confidence & Escalation Gate was not enforced; model bypassed the confidence threshold and issued a verdict from insufficient input rather than abstaining
> **Fix:** Two hard enforcement rules + mandatory evidence completeness pre-check

---

## Purpose

This module adds a mandatory Evidence Completeness Pre-Check that must execute at L4 *before* any verdict path is entered. The benchmark showed the model never returned `InsufficientEvidence` — it always committed to a verdict even when evidence was minimal. This is an over-confidence bias that is particularly dangerous for `Complied` over-assignment (GT: InsufficientEvidence → Pred: Complied was 20/21 cases).

---

## Rule 1 — Mandatory Evidence Completeness Pre-Check (L4 gate)

**Execute before any L5–L12 processing:**

```
EVIDENCE COMPLETENESS PRE-CHECK:

Step 1 — Count objective evidence items:
  objective_evidence_count = len([e for e in objective_evidence
                                  if e is not None and e != "" and
                                  "ไม่พบ" not in e and "ขาด" not in e])

Step 2 — Classify evidence strength:
  IF objective_evidence_count == 0:
      evidence_strength = "absent"
  ELIF evidence contains ONLY procedure/policy/verbal_claim (no records/samples/observations):
      evidence_strength = "policy_only"
  ELIF all provided evidence items are hedged with negative signals
       ("หลักฐานขั้นต่ำ", "ยังไม่สม่ำเสมอ", "บางส่วน", "ไม่พบ"):
      evidence_strength = "weak"
  ELSE:
      evidence_strength = "partial" | "strong" (continue to L5)

Step 3 — Apply gate:
  IF evidence_strength == "absent":
      → verdict = InsufficientEvidence
      → state: "ไม่มีหลักฐานเชิงวัตถุ (objective evidence) เพียงพอสำหรับการตัดสิน"
      → list minimum evidence required
      → STOP. Do NOT proceed to Complied, Noncomplied, OFI, or OBS.

  IF evidence_strength == "policy_only"
     AND clause ∈ implementation_heavy_clauses:
      → verdict = InsufficientEvidence
      → state: "มีเฉพาะ procedure/policy — ยังไม่ได้รับหลักฐานการ implement จริง"
      → list required implementation evidence
      → STOP.

  IF evidence_strength == "weak"
     AND no_breach_signal_present  (i.e., "ไม่พบผลกระทบ" OR "ไม่พบ requirement breach")
     AND positive_system_signal_present (i.e., "ระบบมีอยู่"):
      → verdict = OFI (weak evidence + no breach → improvement opportunity)
      → STOP. Do NOT return Complied without stronger evidence.

  IF evidence_strength == "weak"
     AND breach_signal_present:
      → evidence_strength = "partial"
      → proceed to L5 with caution flag
      → L12 confidence ceiling = 0.79 → ReviewRequired minimum
```

**Implementation-heavy clauses (procedure alone cannot prove Complied):**
```
8.1, 8.2.1, 8.2.2, 8.2.3.1, 8.2.3.2, 8.2.4,
8.3.1, 8.3.2, 8.3.3, 8.3.4, 8.3.5, 8.3.6,
8.4.1, 8.4.2, 8.4.3,
8.5.1, 8.5.2, 8.5.3, 8.5.4, 8.5.5, 8.5.6,
8.6, 8.7.1, 8.7.2,
9.1.1, 9.1.2, 9.2.1, 9.2.2, 9.3.1, 9.3.2, 9.3.3,
10.2.1, 10.2.2
```

---

## Rule 2 — Complied Pre-Condition Checklist (L11 addendum)

Before returning `Complied`, the model MUST confirm all four:

```
COMPLIED PRE-CONDITIONS (all four must be true):

C1 — implementation_proven = true
     Evidence of actual execution, not just a procedure:
     records, samples, observations, performance data, or
     interview WITH corroborating records.

C2 — record_proven = true (for record-requiring clauses)
     At least one verifiable record presented and reviewed.

C3 — evidence covers ALL material requirement elements (not just one element)
     Cross-checked against clause profile (ref 27).

C4 — evidence_age = "current"
     Not stale relative to significant organizational changes.

IF any C1–C4 = false:
    → downgrade to InsufficientEvidence (not Complied, not OFI)
    → state which condition failed
    → list what additional evidence would satisfy the failed condition
```

**Failure mode this prevents:** Benchmark showed 20 GT-InsufficientEvidence cases returned as Complied. These were cases where the scenario had "ระบบมีอยู่และใช้งาน" (positive signal) but the evidence was thin. The model treated positive scenario framing as sufficient — this rule requires C1–C4 proof before Complied can be issued.

---

## Rule 3 — InsufficientEvidence Output Format

When returning `InsufficientEvidence`, include:

```json
{
  "verdict": "InsufficientEvidence",
  "nc_class": null,
  "trigger_or_anchor": "insufficient_evidence",
  "decisive_question_answered": "<which evidence gap caused InsufficientEvidence>",
  "missing_evidence_required": [
    "<item 1: specific record/sample/observation needed>",
    "<item 2: ...>"
  ],
  "next_audit_action": "<one focused question to resolve the gap>"
}
```

Do not return a confidence level above 0.59 for InsufficientEvidence.

---

## Evidence Signal Reference Table

| Evidence pattern in text | evidence_strength | Verdict path |
|---|---|---|
| ตัวอย่าง N รายการ... ไม่พบหลักฐาน + ผู้รับผิดชอบไม่ตรงกับบันทึก | absent | InsufficientEvidence → then NC if breach confirmed |
| มีหลักฐานขั้นต่ำ + ไม่สม่ำเสมอ + ไม่พบผลกระทบ | weak (no breach) | OFI |
| มี procedure แต่ขาดรายละเอียด + ไม่พบการปล่อยงานผิด | policy_only partial | InsufficientEvidence (impl. clause) or Minor D1 |
| ระบบมีอยู่ใช้งาน + หลักฐาน 5 รายการครบถ้วน + สัมภาษณ์ยืนยัน | strong | Complied (after C1–C4 check) |
| ระบบมีอยู่ใช้งาน + หลักฐานขั้นต่ำ (no specific records) | weak | InsufficientEvidence (not Complied) |

---

## SKILL.md Integration — Add to "## Core Behavior" section

```markdown
**Rule added by upskill module `qms-insufficient-evidence-gate-v1`:**

Before any verdict, execute the Evidence Completeness Pre-Check (ref 37):
- If `objective_evidence` is absent or policy-only for an implementation-heavy clause → `InsufficientEvidence`. Do NOT return Complied.
- If evidence is weak with no breach signal → `OFI`. Do NOT return Complied.
- `Complied` requires C1–C4 pre-conditions (ref 37 Rule 2). Confirm all four before returning Complied.
- `InsufficientEvidence` is a valid first-class verdict. Return it whenever evidence does not meet the completeness threshold. Do not "helpfully" resolve evidence gaps toward Complied or NC.
```

---

## F1 Impact Projection

| Metric | Before (v5.1) | Target after (v5.2) |
|---|---|---|
| InsufficientEvidence Recall | 0.000 | ≥ 0.80 |
| InsufficientEvidence F1 | 0.000 | ≥ 0.75 |
| Exact Verdict Macro F1 | 0.686 | ≥ 0.85 |
| Complied over-assignment | 20/21 InsufEv→Complied | ≤ 3/21 |
