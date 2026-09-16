# Severity Anchor Precision — v1.0
> **Upskill module ID:** `qms-severity-anchor-precision-v1`
> **Version:** 1.0.0
> **Addresses:**
> - Major FP = 23 (Minor D2 cases over-escalated to Major — ref 36 Rule 2 fires too broadly)
> - IE FN = 21 (all IE cases still collapsed to Complied/Minor — ref 37/39 not enforced at inference)
> **Benchmark source:** `qms_benchmark_comparison_report.json` — 203 cases
> **Related:** `references/36-major-escalation-gate-v2.md`, `references/38-human-logic-calibration-v1.md`,
> `references/39-ie-complied-boundary-calibration-v1.md`

---

## Part 1 — Root Cause: Two Independent Failures

### Failure 1 — Minor over-escalation (23 cases)

Current ref 36 Rule 2 fires when:
`ไม่มี/ไม่ครบ` + `risk=high` + `mismatch` → presumes Major candidate → runs Q1–Q5

**Problem:** 9 D2 cases have `risk=high` + `non-critical` sector and the same surface signals,
but the **missing item is a sub-element record** (design output, storage record, purchase order),
not an entire process system element. M4 Condition A fails → should stay Minor D2.

**The discriminator the model misses:**

```
M4 = "entire system element absent"
    Examples: no competence process at all, no internal audit programme,
              no CA process at all, no supplier evaluation for ANY supplier

D2 = "process exists, specific record/sub-element gap"
    Examples: design outputs incomplete (process exists, records weak),
              storage records missing (preservation process exists),
              purchase orders incomplete (supplier comm process exists)
```

### Failure 2 — IE still collapsed to Complied (20 cases)

Despite refs 37, 39 being in SKILL.md as rules 8, 16–19, the model still returns
Complied when evidence pattern is `องค์กรแสดง` + `ครบถ้วน สอดคล้อง`.

**Root:** Rules are written correctly but the **enforcement at L4 is not hard enough**.
The rules say "run IE tests A–D" but the model resolves them in favour of Complied
because `ครบถ้วน สอดคล้อง` reads as positive.

**The fix needed: convert IE rules from advisory to HARD STOP.**

---

## Part 2 — Clause Severity Ceiling Table

Data-derived from benchmark: 18 clauses where the correct verdict is **always Minor or lower**
regardless of risk level or mismatch pattern, because their requirement elements are
sub-elements (not entire system elements):

### D2-safe clauses — NEVER Major when missing sub-element records

```
If clause ∈ D2_SAFE_LIST AND ไม่มี/ไม่ครบ pattern:
    → verdict ceiling = Minor (cannot be Major regardless of risk)
    → apply D2 anchor: "process exists, specific record gap"
    → do NOT run Major presumption from ref 36 Rule 2

D2_SAFE_LIST = {
  '4.1',   '4.2',   '5.2.1', '5.2.2',
  '7.1.1', '7.1.3', '7.1.6', '7.3',   '7.4',
  '8.2.3.2', '8.3.3', '8.3.5',
  '8.4.3', '8.5.3', '8.5.4', '8.5.5', '8.5.6',
  '10.1'
}
```

### M4-mandatory clauses — MUST verify M4 when entire process absent

```
If clause ∈ M4_MANDATORY_LIST AND entire-process-absent:
    → M4 presumption applies (ref 36 Rule 2)
    → run Q1–Q5 exhaustively

M4_MANDATORY_LIST = {
  '4.4.2', '5.1.2', '6.1.1', '6.1.2', '6.3',
  '7.2',   '7.5.1', '7.5.2',
  '8.2.2', '8.2.4', '8.3.2', '8.3.4', '8.3.6',
  '8.5.1', '8.7.1', '8.7.2',
  '9.1.1', '9.1.2', '9.2.1', '9.2.2', '9.3.1', '10.2.1'
}
```

### Ambiguous clauses — require deeper evidence check

```
If clause ∈ AMBIGUOUS_LIST:
    → check whether ENTIRE process is absent (→ M4) or records incomplete (→ D2)
    → if unclear → ReviewRequired

AMBIGUOUS_LIST = { '9.1.3', '10.2.2' }
```

---

## Part 3 — Sub-element vs System-element Test

When `ไม่มี/ไม่ครบ` is present, identify what is missing:

```
WHAT IS MISSING TEST (execute at L6 Requirement Element Decomposer):

Ask: Is the missing item a RECORD/SUB-ELEMENT of an existing process,
     or is the ENTIRE PROCESS absent?

RECORD/SUB-ELEMENT (→ D2, not M4):
  "ไม่มี/ไม่ครบ [specific record type]"
  Types: design outputs, design inputs, review minutes, storage records,
         purchase orders, review records, data analysis, CA records,
         process change records, communication records
  Pattern: process context exists → specific required document/record missing

ENTIRE PROCESS (→ M4 candidate):
  "ไม่มี/ไม่ครบ [entire process name]"
  Types: competence matrix (= no competence process),
         KPI reports (= no monitoring process),
         NC output records (= no NC control process),
         audit programme (= no internal audit programme),
         management review schedule (= no review conducted)
  Pattern: no evidence of the process existing at all
```

**Decision:**
```
ENTIRE PROCESS absent + risk=high → M4 → Major
RECORD/SUB-ELEMENT missing + risk=high + non-critical → D2 → Minor
RECORD/SUB-ELEMENT missing + risk=high + critical → D2 → Minor (unless M1/M2/M3 triggered)
```

---

## Part 4 — IE Hard Stop (replaces advisory rules 16–19)

This module converts IE detection from advisory to a **hard stop** that executes
before Complied can be returned:

```
IE HARD STOP — execute at L4 BEFORE returning Complied:

TRIGGER: evidence contains ANY of:
  "องค์กรแสดง"
  "นำเสนอหลักฐาน"
  "ส่งมอบเอกสาร"

When triggered:
  → DO NOT return Complied immediately
  → Run mandatory IE decision chain:

  CHAIN STEP 1: Is audit activity = VERIFIED?
    "ตรวจสอบตัวอย่างหลักฐาน N รายการ" + "ยืนยันระบบทำงานตามที่กำหนด"
    → YES: proceed to Complied check
    → NO (only "องค์กรแสดง"): go to STEP 2

  CHAIN STEP 2: Does "ครบถ้วน สอดคล้อง" appear?
    → YES: this is INTERNAL CONSISTENCY only, not element coverage
    → Does NOT satisfy implementation_proven requirement
    → verdict = InsufficientEvidence

  CHAIN STEP 3: Does "ยืนยันการใช้งานจริง" appear?
    → This is weaker than "ยืนยันระบบทำงานตามที่กำหนด"
    → For implementation-heavy clauses: verdict = InsufficientEvidence
    → For documentation clauses (4.x, 5.2.x, 7.3, 7.4): may proceed to Complied check

  CHAIN STEP 4: Audit type gate
    audit_type = stage_1 + evidence_activity = PRESENTED
    → verdict = InsufficientEvidence (stage_1 = documentation review, not implementation verification)

CHAIN RESULT:
  If any step returns InsufficientEvidence → verdict = InsufficientEvidence
  Do NOT override with Complied
  Required output:
    { "verdict": "InsufficientEvidence",
      "ie_chain_step_failed": "STEP 2/3/4",
      "missing_verification": "ยังไม่มี 'ตรวจสอบตัวอย่าง N รายการ' + 'ยืนยันระบบทำงาน'",
      "next_audit_action": "ขอ sampling deeper / verify implementation at point of use" }
```

---

## Part 5 — Integrated Decision Flow (full v5.5 logic)

```
INPUT: audit evidence text

GATE 0 — Linguistic trigger (ref 39):
  องค์กรแสดง → evidence_activity = PRESENTED
  ตรวจสอบ/สุ่มตรวจ + ยืนยันระบบทำงาน → evidence_activity = VERIFIED
  มี procedure + ขาดรายละเอียด → evidence_activity = PARTIAL → D1 path
  ไม่มี/ไม่ครบ + ไม่พบหลักฐาน → evidence_activity = ABSENT → NC path

GATE 1 — IE Hard Stop (this module Part 4):
  evidence_activity = PRESENTED → run IE chain → InsufficientEvidence (unless chain passes)
  evidence_activity = VERIFIED → proceed to Complied check

GATE 2 — D1 check (evidence_activity = PARTIAL):
  มี procedure + ขาดรายละเอียด + ไม่พบผลกระทบ → Minor D1 (NOT Complied)

GATE 3 — NC path (evidence_activity = ABSENT):
  Check D2_SAFE_LIST (Part 2):
    clause ∈ D2_SAFE_LIST → Minor D2 ceiling (no Major regardless of risk)
    clause ∈ M4_MANDATORY_LIST → run Q1–Q5, M4 presumption
    clause ∈ AMBIGUOUS_LIST → deeper evidence check or ReviewRequired

GATE 4 — Risk × Criticality matrix (ref 38 Part 1.1):
  Only applies when clause ∈ M4_MANDATORY_LIST AND entire process absent
  HIGH_RISK + evidence absent → M4 Major
  MEDIUM_RISK → D2 Minor

GATE 5 — Complied confirmation (C1–C4, ref 37):
  Only reached when evidence_activity = VERIFIED AND IE chain passes
  C1 implementation_proven, C2 record_proven, C3 elements covered, C4 current
  All pass → Complied
  Any fail → InsufficientEvidence with gap statement
```

---

## Part 6 — Updated Regression Suite Additions

Add 8 new cases to `assets/tests/`:

```jsonl
{"case_id":"REG-D2-SAFE-001","clause":"8.3.5","risk_sensitivity":"high","critical_code_status":"non-critical","evidence":"พบว่ากระบวนการของ IAF code 16 ไม่มี/ไม่ครบ design outputs; ตัวอย่าง 3 รายการจากงานจริงไม่พบหลักฐานที่สอดคล้อง และผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก","expected_verdict":"Noncomplied","expected_nc_class":"Minor","expected_trigger":"D2_process_incomplete","test_purpose":"D2-safe clause: 8.3.5 is sub-element, not entire process; risk=high must NOT trigger Major"}
{"case_id":"REG-D2-SAFE-002","clause":"8.5.4","risk_sensitivity":"high","critical_code_status":"non-critical","evidence":"พบว่ากระบวนการของ IAF code 32 ไม่มี/ไม่ครบ storage records; ตัวอย่าง 3 รายการจากงานจริงไม่พบหลักฐาน และผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก","expected_verdict":"Noncomplied","expected_nc_class":"Minor","expected_trigger":"D2_process_incomplete","test_purpose":"D2-safe: preservation record gap is sub-element, cannot be M4"}
{"case_id":"REG-D2-SAFE-003","clause":"8.4.3","risk_sensitivity":"high","critical_code_status":"non-critical","evidence":"พบว่ากระบวนการของ IAF code 7 ไม่มี/ไม่ครบ purchase orders; ตัวอย่าง 3 รายการจากงานจริงไม่พบหลักฐาน และผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก","expected_verdict":"Noncomplied","expected_nc_class":"Minor","expected_trigger":"D2_process_incomplete","test_purpose":"D2-safe: external provider communication record gap is sub-element"}
{"case_id":"REG-M4-STAY-001","clause":"9.1.1","risk_sensitivity":"high","critical_code_status":"non-critical","evidence":"พบว่ากระบวนการของ IAF code 27 ไม่มี/ไม่ครบ KPI reports; ตัวอย่าง 3 รายการจากงานจริงไม่พบหลักฐาน และผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก","expected_verdict":"Noncomplied","expected_nc_class":"Major","expected_trigger":"M4_entire_element_absent","test_purpose":"M4-mandatory: monitoring/KPI = entire process element; must stay Major"}
{"case_id":"REG-M4-STAY-002","clause":"9.2.1","risk_sensitivity":"high","critical_code_status":"critical","evidence":"พบว่ากระบวนการของ IAF code 14 ไม่มี/ไม่ครบ internal audit records; ตัวอย่าง 3 รายการจากงานจริงไม่พบหลักฐาน และผู้รับผิดชอบให้ข้อมูลไม่ตรงกับบันทึก","expected_verdict":"Noncomplied","expected_nc_class":"Major","expected_trigger":"M4_entire_element_absent","test_purpose":"M4-mandatory: internal audit programme = entire system element"}
{"case_id":"REG-IE-HARDSTOP-001","clause":"8.7.2","risk_sensitivity":"high-sensitive","evidence":"สำหรับ IAF code 8 องค์กรแสดง NC log; disposition records; concession approval; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรมของ sector และมีผู้รับผิดชอบยืนยันการใช้งานจริง","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE hard stop: 'องค์กรแสดง' + 'ครบถ้วนสอดคล้อง' triggers IE chain STEP 2; must NOT return Complied"}
{"case_id":"REG-IE-HARDSTOP-002","clause":"4.4.1","risk_sensitivity":"high","audit_type":"stage_1","evidence":"สำหรับ IAF code 11 องค์กรแสดง process map; KPIs; resources; responsibilities; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้อง และมีผู้รับผิดชอบยืนยันการใช้งานจริง","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE hard stop STEP 4: stage_1 + presented evidence = IE, not Complied"}
{"case_id":"REG-IE-HARDSTOP-003","clause":"6.2.2","risk_sensitivity":"medium","evidence":"สำหรับ IAF code 5 องค์กรแสดง objective action plans; responsibility assignments; evaluation records; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรม","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE hard stop: 'ครบถ้วนสอดคล้อง' ≠ implementation verified; medium risk does not override IE gate"}
```

---

## Part 7 — SKILL.md Integration Points

### Add to "★ Layered QMS Audit Cognition Engine" after rule 19:

```markdown
20. **Clause severity ceiling — D2-safe list** *(ref 40 Part 2)* — Before applying Major presumption (ref 36 Rule 2), check if clause is in D2_SAFE_LIST. If yes: verdict ceiling = Minor D2 regardless of risk level. D2-safe clauses have sub-element requirements (records, outputs, inputs, communications), not entire system elements. M4 presumption does NOT apply.

21. **Sub-element vs system-element test** *(ref 40 Part 3)* — When `ไม่มี/ไม่ครบ` pattern present, identify what is missing: if a RECORD/SUB-ELEMENT (design outputs, storage records, purchase orders, etc.) → D2 ceiling. If ENTIRE PROCESS absent (no competence process, no audit programme, no NC control) → M4 candidate.

22. **IE Hard Stop — override all Complied returns** *(ref 40 Part 4)* — When `องค์กรแสดง` pattern detected, run the 4-step IE decision chain before any Complied verdict is returned. `ครบถ้วน สอดคล้อง` alone (STEP 2) → InsufficientEvidence. `ยืนยันการใช้งานจริง` alone for implementation-heavy clauses (STEP 3) → InsufficientEvidence. stage_1 + presented evidence (STEP 4) → InsufficientEvidence. Chain must PASS all steps before Complied is permitted.
```

### Update route matrix:
Add `40` to `nc_classification` and `conformity_evaluation` routes.

---

## Part 8 — Release Gate Projection

| Metric | v5.4 actual | v5.5 target |
|---|---|---|
| Major Precision | 0.566 | ≥ 0.90 |
| Major Recall | 1.000 | ≥ 0.88 (maintain) |
| InsufficientEvidence Recall | 0.000 | ≥ 0.80 |
| Composite Macro F1 | 0.660 | ≥ 0.85 |
| Minor F1 | 0.826 | ≥ 0.90 |
| Binary NC Precision | 0.991 | ≥ 0.99 (maintain) |
| Binary NC Recall | 1.000 | 1.000 (maintain) |
| Clause accuracy | 1.000 | 1.000 (maintain) |
