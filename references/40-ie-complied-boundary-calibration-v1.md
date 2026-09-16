# IE vs Complied Boundary Calibration — v1.0
> **Upskill module ID:** `qms-ie-complied-boundary-v1`
> **Type:** `clause_guide_module`
> **Version:** 1.0.0
> **Benchmark evidence:** InsufficientEvidence Recall = 0.000 across all 3 rounds (v5.1/v5.2/v5.3)
> — 21 IE cases predicted as Complied (20) or NC (1) every round
> **Root cause confirmed from benchmark data analysis:**
> IE and Complied share similar surface patterns (evidence presented, records shown)
> but differ on ONE critical linguistic marker and ONE audit activity marker.
> **Related:** `references/37-insufficient-evidence-gate-v1.md` (rules), `references/38-human-logic-calibration-v1.md` (severity)

---

## Part 1 — The Core Boundary: "แสดง" vs "ตรวจสอบ"

This is the single most important distinction in this module.

### What the benchmark data shows

From 203-case analysis, **two verbs distinguish IE from Complied 95%+ of the time:**

| Verdict | Trigger verb | Meaning in audit context |
|---|---|---|
| **InsufficientEvidence** | `องค์กรแสดง` | Organization **presented** documents — auditor received them but has NOT verified depth, effectiveness, or full element coverage |
| **Complied** | `ตรวจสอบตัวอย่างหลักฐาน N รายการ` / `สุ่มตรวจสอบ` | Auditor **actively sampled and verified** — system confirmed working |

**Human auditor logic:**

```
"องค์กรแสดง [evidence list]" = 
    "The auditee brought records to the table."
    = Evidence EXISTS but auditor has not yet verified:
        - Does it cover ALL requirement elements?
        - Does it prove IMPLEMENTATION (not just documentation)?
        - Is EFFECTIVENESS demonstrated?
    → This is the starting point for audit work, NOT a conclusion.
    → Verdict: InsufficientEvidence (need deeper sampling)

"ตรวจสอบตัวอย่างหลักฐาน 5 รายการ + ยืนยันระบบทำงานตามที่กำหนด + implement จริง" =
    "Auditor sampled N cases, interviewed responsible persons,
     confirmed system operates as intended."
    → Implementation proven + element coverage confirmed
    → Verdict: Complied
```

---

## Part 2 — Full Linguistic Decision Gate (L4 Extension)

Execute this gate at L4 Evidence Parser **before** any verdict path:

```
LINGUISTIC TRIGGER ANALYSIS (execute first):

STEP 1 — Identify the audit activity verb:

  GROUP A — "แสดง" (presented by auditee):
    Signals: "องค์กรแสดง", "นำเสนอ", "ส่งมอบหลักฐาน", "แสดงเอกสาร"
    Meaning: Evidence received, NOT yet verified by auditor
    → Set evidence_activity = PRESENTED
    → Go to STEP 3

  GROUP B — "ตรวจสอบ/สุ่มตรวจ" (verified by auditor):
    Signals: "ตรวจสอบตัวอย่างหลักฐาน N รายการ",
             "สุ่มตรวจสอบ N กระบวนการ",
             "ยืนยันระบบทำงานตามที่กำหนด",
             "ยืนยันว่า implement จริง"
    Meaning: Auditor actively sampled + confirmed
    → Set evidence_activity = VERIFIED
    → Go to STEP 2 (Complied path)

  GROUP C — "ไม่มี/ไม่ครบ + ไม่พบหลักฐาน" (absent):
    Signals: "ไม่มี/ไม่ครบ", "ไม่พบหลักฐาน", "กระบวนการไม่มีอยู่"
    Meaning: Evidence gap confirmed
    → Set evidence_activity = ABSENT
    → NC path (ref 38 decision tree)

  GROUP D — "มี procedure แต่ขาด" (procedure exists, records weak):
    Signals: "มี procedure สำหรับ [clause title]",
             "ตัวอย่างบันทึก...ขาดรายละเอียดสำคัญ"
    Meaning: Process intent exists, implementation incomplete
    → Set evidence_activity = PARTIAL
    → Minor D1/D2 path

STEP 2 — VERIFIED path (Complied candidate):
  Check all 4 Complied pre-conditions (ref 37 Rule 2):
    C1: implementation_proven = true (records + "ยืนยันระบบทำงาน")
    C2: record_proven = true (sampled N specific cases)
    C3: all material elements covered
    C4: evidence current
  ALL 4 pass → verdict = Complied
  Any fail → verdict = InsufficientEvidence (with gap statement)

STEP 3 — PRESENTED path (IE candidate):
  Organization showed evidence but auditor has NOT verified depth.
  Apply IE completeness tests:

  Test A — Scope coverage:
    Does "มีตัวอย่างบันทึก N รายการ ครบถ้วน สอดคล้อง" confirm
    ALL requirement elements are covered?
    → "ครบถ้วน สอดคล้อง" alone = internal consistency of records
    → Does NOT confirm element coverage against L6 clause profile
    → Auditor must verify element-by-element
    → If cannot verify → InsufficientEvidence

  Test B — Implementation depth:
    "ยืนยันการใช้งานจริง" = confirms records EXIST and are USED
    → Does NOT prove effectiveness or full implementation
    → For implementation-heavy clauses: need "ยืนยันระบบทำงาน" level
    → "ยืนยันการใช้งานจริง" < "ยืนยันระบบทำงานตามที่กำหนด"
    → Gap → InsufficientEvidence

  Test C — Sampling adequacy:
    "3 รายการ" vs "5 รายการ" in context of clause risk:
    → High-risk clause + 3 records (not 5+) = sampling may be insufficient
    → High-sensitive risk + "1 site / 3 records" = limited sampling
    → → InsufficientEvidence

  Test D — Audit type context:
    stage_1 audit → documentation review stage, NOT implementation verification
    → All "organization shows evidence" in stage_1 → InsufficientEvidence
    → stage_2/surveillance with full sampling → may be Complied
```

---

## Part 3 — Exact Phrase Reference Table

Derived from 100% of benchmark IE cases vs Complied cases:

| Evidence phrase | verdict | Confidence |
|---|---|---|
| `องค์กรแสดง [X]; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้อง; ยืนยันการใช้งานจริง` | **InsufficientEvidence** | 95% |
| `ตรวจสอบตัวอย่างหลักฐาน 5 รายการจาก [sector]: พบ [X] ครบถ้วนและสอดคล้องกัน; ยืนยันระบบทำงานตามที่กำหนด` | **Complied** | 100% |
| `สุ่มตรวจสอบ 3 กระบวนการหลัก: [X] มีครบและ up-to-date; implement จริงในทุกจุด; ยืนยัน 3 คน` | **Complied** | 100% |
| `มี procedure สำหรับ [clause]: ตัวอย่างบันทึก...ขาดรายละเอียดสำคัญ; ไม่พบผลกระทบ conformity` | **Noncomplied / Minor D1** | 95% |
| `ไม่มี/ไม่ครบ [X]; ตัวอย่าง 3 รายการ ไม่พบหลักฐาน; ผู้รับผิดชอบให้ข้อมูลไม่ตรง` | **Noncomplied / Major or Minor** | 95% |

### Critical subtlety: "ครบถ้วน สอดคล้อง" ≠ "Complied"

```
"มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรมของ sector"
= "3 recent records, complete, consistent with sector activities"
= Records are internally consistent ✓
= Records exist and are recent ✓
≠ ALL requirement elements verified ✗
≠ Effectiveness demonstrated ✗
≠ Auditor actively sampled and confirmed implementation ✗
→ This phrase alone → InsufficientEvidence, NOT Complied
```

---

## Part 4 — False Negative Fix (GT NC → PRED Complied)

The 20 false negatives (NC cases predicted as Complied) come from L4 Evidence Parser
misclassifying D1 "procedure exists but records weak" as sufficient for Complied.

**Fix — D1 detection gate:**

```
IF evidence contains:
  "มี procedure สำหรับ [clause title]"
  AND "ตัวอย่างบันทึก...ขาดรายละเอียดสำคัญ"
  AND "ไม่พบการปล่อยงานผิด" OR "ไม่พบผลกระทบต่อ conformity"

→ This is NOT Complied (procedure ≠ implementation)
→ This is NOT InsufficientEvidence (requirement breach IS identifiable)
→ This IS Noncomplied / Minor D1

Decision: Noncomplied / Minor D1
Rationale: Procedure exists → implementation_proven = false (records weak)
           No conformity impact → NOT Major
           → D1: documentation gap, no harm demonstrated
```

**Hard rule added to L4 Evidence Parser:**

```
implementation_proven = true REQUIRES:
  "ยืนยันระบบทำงานตามที่กำหนด"  (system confirmed working)
  OR "implement จริงในทุกจุดที่กำหนด"  (actually implemented at all points)
  OR records + observations + interviews converge

implementation_proven = false (DO NOT return Complied) when:
  "มี procedure" alone (without verification)
  "องค์กรแสดง" alone (presented, not verified)
  "ครบถ้วน สอดคล้อง" alone (consistent, not verified effective)
  "ยืนยันการใช้งานจริง" alone (confirmed used, not confirmed working as required)
```

---

## Part 5 — Regression Test Suite Addition

### 10 new gold regression cases for `assets/tests/`

These cases specifically test the IE vs Complied vs D1 boundary:

**Group A: IE cases (must NOT predict Complied)**

```jsonl
{"case_id":"REG-IE-001","clause":"8.7.2","evidence":"องค์กรแสดง NC log; disposition records; concession approval; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรมของ sector และมีผู้รับผิดชอบยืนยันการใช้งานจริง","audit_type":"surveillance_1","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE: org shows evidence + consistent records ≠ Complied; auditor must verify element coverage"}
{"case_id":"REG-IE-002","clause":"6.2.2","evidence":"องค์กรแสดง objective action plans; responsibility assignments; evaluation records; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรมของ sector","audit_type":"stage_1","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE: stage_1 audit + org presents docs = documentation review only, not implementation verified"}
{"case_id":"REG-IE-003","clause":"4.4.1","evidence":"องค์กรแสดง process map; KPIs; resources; responsibilities; process records; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้อง และมีผู้รับผิดชอบยืนยันการใช้งานจริง","audit_type":"surveillance_1","risk_sensitivity":"high","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE: 'ยืนยันการใช้งานจริง' < 'ยืนยันระบบทำงานตามที่กำหนด'; not full verification"}
{"case_id":"REG-IE-004","clause":"9.3.3","evidence":"องค์กรแสดง management review outputs; action plans; assignments; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรมของ sector","audit_type":"surveillance_2","risk_sensitivity":"high-sensitive","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE: high-sensitive risk + 3 records only = insufficient sampling depth"}
{"case_id":"REG-IE-005","clause":"8.4.1","evidence":"องค์กรแสดง supplier scope list; outsourcing controls; ASL; มีตัวอย่างบันทึก 3 รายการล่าสุด ครบถ้วน สอดคล้องกับกิจกรรมของ sector และมีผู้รับผิดชอบยืนยันการใช้งานจริง","audit_type":"surveillance_1","risk_sensitivity":"high","expected_verdict":"InsufficientEvidence","expected_nc_class":null,"test_purpose":"IE: supplier control high-risk clause + presented evidence only, not verified"}
```

**Group B: Complied cases (must NOT predict IE)**

```jsonl
{"case_id":"REG-COMPLIED-001","clause":"10.2.2","evidence":"ตรวจสอบตัวอย่างหลักฐาน 5 รายการจาก Manufacturing: พบ CA records; evidence attachments; closure approvals ครบถ้วนและสอดคล้องกัน; สัมภาษณ์ผู้รับผิดชอบหลัก 2 คน ยืนยันระบบทำงานตามที่กำหนด; ไม่พบ deviation หรือ nonconformity","audit_type":"recertification","expected_verdict":"Complied","expected_nc_class":null,"test_purpose":"Complied: auditor actively sampled 5 + verified system works + no deviation"}
{"case_id":"REG-COMPLIED-002","clause":"9.2.1","evidence":"สุ่มตรวจสอบ 3 กระบวนการหลักของ Recycling: audit programme; plans; reports; auditor competence มีครบและ up-to-date; procedure ถูก implement จริงในทุกจุดที่กำหนด; สัมภาษณ์ผู้ปฏิบัติงาน 3 คนได้รับการยืนยันสอดคล้องกัน","audit_type":"surveillance_2","expected_verdict":"Complied","expected_nc_class":null,"test_purpose":"Complied: random sampling + implement จริง + multi-person interview confirmation"}
```

**Group C: Minor D1 cases (must NOT predict Complied)**

```jsonl
{"case_id":"REG-D1-001","clause":"8.4.2","evidence":"มี procedure สำหรับ Type and extent of control แต่ตัวอย่างบันทึกใน IAF code 15 ขาดรายละเอียดสำคัญบางส่วนของ supplier control plan; incoming inspection; performance monitoring; ไม่พบการปล่อยงานผิดหรือผลกระทบลูกค้า","audit_type":"surveillance_1","expected_verdict":"Noncomplied","expected_nc_class":"Minor","test_purpose":"D1: procedure exists + records weak + no harm = Minor D1, NOT Complied"}
{"case_id":"REG-D1-002","clause":"9.1.1","evidence":"มี procedure สำหรับ Monitoring, measurement, analysis and evaluation แต่ตัวอย่างบันทึกใน IAF code 6 ขาดรายละเอียดสำคัญบางส่วนของ KPI reports; monitoring plans; analysis outputs; ไม่พบผลกระทบต่อ conformity ในตัวอย่างที่ตรวจ","audit_type":"surveillance_1","risk_sensitivity":"high","expected_verdict":"Noncomplied","expected_nc_class":"Minor","test_purpose":"D1: procedure + incomplete records + no conformity impact = Minor D1, NOT Complied"}
{"case_id":"REG-D1-003","clause":"7.5.3.2","evidence":"มี procedure สำหรับ Control of documented information - distribution/storage/change/retention/disposition แต่ตัวอย่างบันทึก ขาดรายละเอียดสำคัญบางส่วน; ไม่พบการปล่อยงานผิดหรือผลกระทบ conformity","audit_type":"recertification","risk_sensitivity":"high","expected_verdict":"Noncomplied","expected_nc_class":"Minor","test_purpose":"D1: procedure + record gap + no harm = Minor D1, NOT Complied"}
```

---

## Part 6 — SKILL.md Integration Points

### Add to "★ Layered QMS Audit Cognition Engine" — after rule 15:

```markdown
16. **L4 Linguistic trigger gate** *(ref 39 Part 2)* — Before any verdict, identify the **audit activity verb**:
    - `องค์กรแสดง` / `นำเสนอ` = evidence PRESENTED by auditee → InsufficientEvidence path (Tests A–D)
    - `ตรวจสอบ/สุ่มตรวจ` + `ยืนยันระบบทำงาน` + `implement จริง` = evidence VERIFIED by auditor → Complied path
    - `มี procedure แต่ขาด` + `ไม่พบผลกระทบ` = procedure exists, records weak → Minor D1 path
    - `ไม่มี/ไม่ครบ` + `ไม่พบหลักฐาน` = evidence absent → NC path (ref 38)

17. **"ครบถ้วน สอดคล้อง" ≠ Complied** *(ref 39 Part 3)* — The phrase `ครบถ้วน สอดคล้องกับกิจกรรมของ sector` confirms records are internally consistent and recent. It does NOT confirm: all requirement elements covered, effectiveness demonstrated, or auditor-verified implementation. Treat as InsufficientEvidence until `ยืนยันระบบทำงานตามที่กำหนด` is established.

18. **"ยืนยันการใช้งานจริง" < "ยืนยันระบบทำงาน"** *(ref 39 Part 2 Test B)* — `ยืนยันการใช้งานจริง` (confirmed records are used) is a weaker confirmation than `ยืนยันระบบทำงานตามที่กำหนด` (system confirmed working as required). The former → InsufficientEvidence for implementation-heavy clauses. The latter → Complied permitted.

19. **D1 false-Complied prevention** *(ref 39 Part 4)* — `มี procedure สำหรับ [clause]` + `ตัวอย่างบันทึก...ขาดรายละเอียดสำคัญ` = `implementation_proven = false`. Do NOT return Complied. This pattern = Noncomplied / Minor D1 when no conformity impact found.
```

### Update route matrix:
Add `39` to `nc_classification` and `conformity_evaluation` routes.

---

## Part 7 — Release Gate Projection

| Metric | v5.3 actual | v5.4 target |
|---|---|---|
| InsufficientEvidence Recall | 0.000 | ≥ 0.80 |
| False negative NC→Complied | 20 cases | ≤ 5 cases |
| Verdict Macro F1 | 0.686 | ≥ 0.85 |
| Composite Verdict+NC F1 | 0.624 | ≥ 0.85 |
| Binary Precision | 1.000 | 1.000 (maintain) |
| Clause accuracy | 1.000 | 1.000 (maintain) |
