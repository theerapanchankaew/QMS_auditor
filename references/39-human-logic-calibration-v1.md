# QMS Human Logic Calibration — v1.0
> **Upskill module ID:** `qms-human-logic-calibration-v1`
> **Type:** `clause_guide_module`
> **Version:** 1.0.0
> **Addresses benchmark failures:**
> - Major Precision = 0.566 (target ≥ 0.90) — over-escalation to Major
> - InsufficientEvidence Recall = 0.000 — verdict forced when evidence ambiguous
> - Composite Verdict+NC Macro F1 = 0.825 (target ≥ 0.85)
> **Benchmark source:** `qms_synth_v3_benchmark_report.md` — 203 cases, 65 clauses, 39 IAF sectors

---

## Purpose

This module defines the **human auditor decision logic** that separates four verdict/severity classes
whose surface evidence patterns look identical but require different judgements:

| Class | Surface signal | True discriminator |
|---|---|---|
| **Major / M4** | ไม่มี/ไม่ครบ + mismatch | risk HIGH + critical sector OR entire process absent |
| **Minor / D2** | ไม่มี/ไม่ครบ + mismatch | risk MEDIUM + non-critical sector, process incomplete not absent |
| **Minor / D1** | procedure exists, records weak | process exists, documentation gap only |
| **InsufficientEvidence** | evidence presented, complete, consistent | evidence is there but scope/effectiveness ambiguous |

The model must learn that **surface text is not the verdict** — the risk level, sector criticality,
and nature of the gap (absent vs incomplete vs ambiguous) are the actual controls.

---

## Part 1 — Major / Minor Severity Discriminator

### 1.1 The two-axis decision matrix

Derived from 203-case benchmark analysis. M4 and D2 cases share identical surface signals
(`ไม่มี/ไม่ครบ` + interview mismatch) but split cleanly on two axes:

```
                    critical_code_status
                    critical    non-critical
                 ┌────────────┬─────────────┐
risk  high /     │   MAJOR    │   MAJOR*    │
      high-sens  │    M4      │    M4       │
                 ├────────────┼─────────────┤
risk  medium /   │   MINOR    │   MINOR     │
      medium-high│    D2      │    D2       │
                 └────────────┴─────────────┘

* high + non-critical: 9/27 Major cases — M4 confirmed by entire-element-absent pattern
```

**Decision rule (execute before any severity assignment when `ไม่มี/ไม่ครบ` pattern present):**

```
STEP 1 — Classify risk level:
  high / high-sensitive / very high  → HIGH_RISK = true
  medium / medium-high               → HIGH_RISK = false

STEP 2 — Classify sector criticality:
  critical_code_status = critical    → CRITICAL_SECTOR = true
  critical_code_status = non-critical → CRITICAL_SECTOR = false

STEP 3 — Apply matrix:
  IF HIGH_RISK = true AND CRITICAL_SECTOR = true  → presumptive MAJOR; validate M-trigger
  IF HIGH_RISK = true AND CRITICAL_SECTOR = false → presumptive MAJOR; validate M-trigger
  IF HIGH_RISK = false (regardless of sector)     → presumptive MINOR D2; validate no M-trigger
```

### 1.2 M4 "entire element absent" precision rule

**The core over-escalation cause:** Model interprets "ไม่มี/ไม่ครบ" as M4 (entire element absent)
even when the evidence says the process *exists* but is *incomplete*.

**Human auditor logic — M4 requires ALL THREE:**

```
M4 = ENTIRE element absent. Requires:

  Condition A: No process at all
    "กระบวนการไม่มีอยู่" / "ไม่เคยจัดทำ" / "ไม่พบการดำเนินการใดๆ"
    NOT "มีบ้าง แต่ไม่ครบ" / "มีบางส่วน" / "ยังไม่สม่ำเสมอ"

  Condition B: No records exist (not just incomplete)
    ตัวอย่าง N รายการ → ไม่พบหลักฐาน (zero evidence found)
    NOT: พบหลักฐานบางส่วนแต่ไม่ครบ

  Condition C: Interview mismatch confirms absence
    ผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก
    = confirms the gap is real, not a sampling issue

  ALL THREE → M4 (Major)
  B + C but NOT A (process exists weakly) → D2 (Minor)
  Only C → insufficient for severity alone
```

### 1.3 "Process incomplete" = D2, not M4

**Explicit boundary statements:**

| Evidence phrase | Correct classification |
|---|---|
| `ไม่มี/ไม่ครบ` + `ตัวอย่าง N รายการจากงานจริงไม่พบหลักฐาน` + mismatch + HIGH_RISK | **Major M4** |
| `ไม่มี/ไม่ครบ` + `ตัวอย่าง N รายการจากงานจริงไม่พบหลักฐาน` + mismatch + MEDIUM_RISK | **Minor D2** |
| `มี procedure แต่ขาดรายละเอียด` + `ไม่พบการปล่อยงานผิด` | **Minor D1** |
| `มีบางส่วน` + `ยังไม่สม่ำเสมอ` + no mismatch | **Minor D2** |
| `องค์กรแสดง [evidence items] ครบถ้วน สอดคล้อง` | **InsufficientEvidence** (see Part 2) |

---

## Part 2 — InsufficientEvidence Detection

### 2.1 The counter-intuitive pattern

**InsufficientEvidence does NOT mean "no evidence."**
In 20/21 benchmark IE cases, the organization **showed evidence** — but the evidence was
ambiguous enough that no confident verdict could be reached.

**InsufficientEvidence signal pattern (benchmark-derived):**

```
STRONG IE SIGNALS (present in 95%+ of IE cases):
  "องค์กรแสดง [list of evidence items]"  ← evidence IS presented
  "มีตัวอย่างบันทึก N รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรม"  ← records look complete
  Absence of: "ไม่มี/ไม่ครบ", "ผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก"

MEANING: Evidence is present and internally consistent, but:
  - Scope is unclear (does it cover all required elements?)
  - Effectiveness cannot be verified from records alone
  - Traceability to requirement elements is incomplete
  - Confidence < 0.80 even after full L4–L11 evaluation
```

### 2.2 InsufficientEvidence decision gate

```
EXECUTE when: evidence is presented but confidence < 0.80

Test 1 — Evidence completeness:
  Does evidence cover ALL material requirement elements per L6?
  → YES on all elements → proceed to verdict (Complied or NC)
  → NO on any material element → InsufficientEvidence

Test 2 — Implementation verification:
  For implementation-heavy clauses (8.x, 9.x, 10.x):
  Is implementation_proven = true (records, samples, observations)?
  → NO → InsufficientEvidence
  (Do NOT return Complied from records-look-complete alone)

Test 3 — Scope/effectiveness traceability:
  Can the evidence be traced to specific requirement elements?
  → Cannot trace → InsufficientEvidence with gap statement

Test 4 — Confidence gate (L12):
  After L4–L11 evaluation, confidence level?
  → < 0.60 → InsufficientEvidence
  → 0.60–0.79 → ReviewRequired
  → ≥ 0.80 → proceed to verdict
```

### 2.3 IE vs Complied — do not collapse

**The most damaging error in v5.1 benchmark:** 20/21 IE cases were predicted as Complied.

**Human auditor test before returning Complied:**

```
Ask: "If I were to write a Complied finding, what exact requirement elements
      am I saying are met, and what specific evidence proves each one?"

  Can answer for ALL elements → Complied permitted
  Cannot answer for any element → InsufficientEvidence, not Complied
  Can answer partially → InsufficientEvidence with specific gap
```

---

## Part 3 — Consolidated Severity Decision Tree

Full decision tree incorporating all benchmark-calibrated rules:

```
START: Noncomplied candidate identified (L8 breach confirmed)

┌─ STEP 1: Evidence pattern check ─────────────────────────────┐
│                                                               │
│  "ไม่มี/ไม่ครบ" present?                                     │
│  YES → go to STEP 2                                           │
│  NO  → go to STEP 4 (D1/D2 path)                             │
└───────────────────────────────────────────────────────────────┘

┌─ STEP 2: Risk + Criticality matrix ──────────────────────────┐
│                                                               │
│  risk_sensitivity ∈ {high, high-sensitive, very high}?        │
│  YES → HIGH_RISK                                              │
│  NO  → MEDIUM_RISK → go to MINOR D2 (STEP 5)                 │
└───────────────────────────────────────────────────────────────┘

┌─ STEP 3: M4 validation (HIGH_RISK path only) ─────────────────┐
│                                                               │
│  A: Process completely absent? (NOT incomplete — ABSENT)      │
│  B: Zero records found in N samples?                          │
│  C: Interview mismatch confirms absence?                      │
│                                                               │
│  ALL THREE → MAJOR M4                                         │
│  B + C but A unclear → run Q1–Q5 full exposure (ref 36)       │
│  Only C → HIGH_RISK + non-critical → run Q1–Q5               │
│  None → MINOR D2                                              │
└───────────────────────────────────────────────────────────────┘

┌─ STEP 4: D1 check (procedure exists) ────────────────────────┐
│                                                               │
│  "มี procedure" present?                                     │
│  YES + "ไม่พบผลกระทบ" or "ไม่พบการปล่อยงานผิด" → MINOR D1  │
│  YES + breach signal present → MINOR D2                      │
└───────────────────────────────────────────────────────────────┘

┌─ STEP 5: Minor D2 confirmation ──────────────────────────────┐
│                                                               │
│  Process exists but incomplete?                               │
│  YES → MINOR D2                                               │
│  Unclear → ReviewRequired                                     │
└───────────────────────────────────────────────────────────────┘

┌─ ADDITIONAL: InsufficientEvidence path ──────────────────────┐
│                                                               │
│  "องค์กรแสดง" + "ครบถ้วน สอดคล้อง" pattern?                 │
│  → Run IE Tests 1–4 (Part 2.2)                               │
│  → confidence < 0.80 → InsufficientEvidence                  │
│  → Do NOT force verdict when scope/traceability unclear       │
└───────────────────────────────────────────────────────────────┘
```

---

## Part 4 — Clause-Specific Major/Minor Override Table

Benchmark-calibrated overrides. Use AFTER decision tree as final check:

| Clause | Major trigger | Minor anchor | Key discriminator |
|---|---|---|---|
| 7.2 | M4 (no competence process at all) or M1 (unqualified person on critical process) | D2 (process exists but gap) | Is the **person performing** a critical process unqualified? → M1 |
| 7.5.1/7.5.2 | M4 (document control entirely absent) or M1 (undocumented critical parameter) | D1 (one record missing/unsigned) | Is a **critical production parameter** controlled only by undocumented verbal instruction? → M1 |
| 8.3.2/8.3.6 | M4 (D&D process absent when applicable), M3 (unverified design released) | D2 (process exists, one phase weak) | Was design **released without verification**? → M3 |
| 9.1.1 | M4 (no monitoring process), M1 (release-affecting measurement absent) | D2 (monitoring exists but weak) | Is monitoring absent for **release decisions**? → M1/M3 |
| 9.2.1/9.2.2 | M4 (no audit programme), M5 (previous NC excluded from follow-up) | D2 (programme exists, some areas missed) | Were **previous NCs excluded** from follow-up? → M5 |
| 9.3.1 | M4 (no management review conducted ever) | D2 (review done but inputs missing) | Has management review **never been conducted**? → M4 |
| 6.1.1 | M4 (no R&O planning), M1 (risk materialized) | D2 (risks identified, no actions) | Did a risk **materialize** without controls? → M1 |
| 4.4.2 | M4 (no documented QMS process at all) | D2 (QMS documented but one process missing) | Is the **entire QMS documentation** absent? → M4 |
| 10.2.2 | M5 (repeated NC after CA closure) | D2 (CA exists, effectiveness review weak) | Is this the **same NC recurring** after verified CA? → M5 |
| 5.1.2 | M4 (customer focus entirely absent) | D2 (exists but inconsistent) | Is there **zero evidence** of customer focus activities? → M4 |

---

## Part 5 — Required Output Format for Calibrated Verdicts

Every NC verdict must now include the calibration trace:

```json
{
  "verdict": "Noncomplied",
  "nc_class": "Major | Minor",
  "trigger_or_anchor": "M1–M5 | D1–D4",
  "decisive_question_answered": "<the single question that controlled severity>",
  "calibration_trace": {
    "risk_sensitivity": "<value from case>",
    "critical_code_status": "<value from case>",
    "evidence_pattern": "absent | incomplete | policy_only | presented_ambiguous",
    "m4_conditions_checked": {
      "A_process_entirely_absent": true | false,
      "B_zero_records_in_samples": true | false,
      "C_interview_mismatch_confirms": true | false
    },
    "severity_path": "risk_matrix → M4_validation | D2_direct | D1_direct | IE_path"
  }
}
```

For `InsufficientEvidence`:
```json
{
  "verdict": "InsufficientEvidence",
  "nc_class": null,
  "trigger_or_anchor": "insufficient_evidence",
  "decisive_question_answered": "<which IE test failed>",
  "calibration_trace": {
    "evidence_pattern": "presented_ambiguous",
    "ie_test_failed": "Test 1 | Test 2 | Test 3 | Test 4",
    "missing_evidence_required": ["<item 1>", "<item 2>"],
    "confidence_at_decision": "<value below 0.80>"
  }
}
```

---

## Part 6 — SKILL.md Integration Points

### Add to "★ Layered QMS Audit Cognition Engine" — after rule 11:

```markdown
12. **Severity discriminator — risk×criticality matrix** *(ref 38 Part 1.1)* — When `ไม่มี/ไม่ครบ` pattern present, determine severity by TWO axes before any M-trigger check:
    - `risk_sensitivity ∈ {high, high-sensitive, very high}` = HIGH_RISK
    - `risk_sensitivity ∈ {medium, medium-high}` = MEDIUM_RISK → Minor D2 (unless M-trigger found)
    - HIGH_RISK → validate M4 three-condition test (ref 38 Part 1.2)

13. **M4 three-condition test** *(ref 38 Part 1.2)* — M4 requires ALL THREE: (A) process entirely absent, not merely incomplete; (B) zero records found in samples; (C) interview mismatch confirms. Missing any condition → do not assign M4; use D2 or ReviewRequired.

14. **InsufficientEvidence counter-intuitive pattern** *(ref 38 Part 2.1)* — IE is triggered by `องค์กรแสดง [evidence] ครบถ้วน สอดคล้อง` pattern (evidence IS present but scope/traceability ambiguous), NOT by evidence absence. Evidence absence triggers NC path. Presented-but-ambiguous evidence triggers IE path.

15. **Calibration trace required** *(ref 38 Part 5)* — Every NC verdict must include `calibration_trace` with risk_sensitivity, critical_code_status, evidence_pattern, M4 conditions checked, and severity_path taken.
```

### Update route matrix:
- `nc_classification`: add `38` to mandatory load
- `conformity_evaluation`: add `38` to mandatory load

---

## Part 7 — Release Gate Targets After This Module

| Metric | v5.1 | v5.2 (post ref36/37) | v5.3 target |
|---|---|---|---|
| Major Precision | 0.941 | 0.566 *(over-corrected)* | ≥ 0.90 |
| Major Recall | 0.533 | 1.000 | ≥ 0.88 |
| Major F1 | ~0.69 | ~0.72 | ≥ 0.89 |
| InsufficientEvidence Recall | 0.000 | 0.000 | ≥ 0.80 |
| Exact Verdict Macro F1 | 0.686 | 0.915 | ≥ 0.92 |
| Composite Verdict+NC F1 | 0.668 | 0.825 | ≥ 0.85 |
| NC Class Macro F1 | 0.861 | 0.848 | ≥ 0.90 |

