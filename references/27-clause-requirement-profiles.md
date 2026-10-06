# QMS Clause Requirement Profiles — ISO 9001:2026 v1.0
> **Purpose:** Provide per-clause requirement element lists for L6 (Requirement Element Decomposer).
> **Usage:** Load the relevant clause profile at L6 before evaluating any case. Check each element independently.
> **Implementation-heavy clauses** (policy alone insufficient): 8.3, 8.4, 8.5, 8.6, 8.7, 9.2, 10.2
> **Index:** 4.1 | 4.2 | 5.1 | 5.2 | 6.1 | 6.2 | 6.3 | 7.1.5 | 7.2 | 7.3 | 7.4 | 7.5 | 8.1 | 8.3 | 8.4 | 8.5 | 8.6 | 8.7 | 9.1 | 9.2 | 9.3 | 10.2

> **Reconciliation note (2026-10-06).** The `Conditional?` column was checked against the registered text of ISO 9001:2026 (`assets/standards/ISO_9001_2026.pdf`). It is a per-element summary and is **not complete**: the full list of clauses whose text carries a qualifier phrase, with the exact wording, is `references/standard/iso9001-2026-standard-map.md` → “Conditional qualifiers in clauses 4–10” (22 clauses; this file annotates only part of them — e.g. 4.3, 4.4.2, 5.2.2, 6.2.1, 7.2, 7.1.6, 8.1, 8.2.x, 8.3.5, 8.3.6, 8.5.1, 8.5.6, 8.6, 9.1.1 and 10.2.1 carry none here). Cells whose label did not match the text were corrected below; cells marked “by circumstance” are conditional only because the activity may not exist or a stated condition may not hold — the text has no qualifier phrase there. The verdict rule for conditional elements is the L7 gate (`SKILL.md`, `references/26-layered-audit-cognition.md`); nothing in this note changes it.

---

## Clause 4.1 — Context of the Organization

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | External issues determined (market, regulatory, societal, technological) | Documented analysis | No |
| 2 | Internal issues determined (culture, capabilities, knowledge, performance) | Record | No |
| 3 | Issues monitored and reviewed | Review records | No |
| 4 | Climate change and its relevance to QMS considered (2026) | Documentation or explicit exclusion rationale | No |
| 5 | Quality culture and ethical behaviour considered (2026) | Policy, culture assessment, leadership evidence | No |

**Common failure:** Climate change or quality culture element not considered → Minor D2.
**Major M4:** No context analysis process at all.

---

## Clause 4.2 — Interested Parties

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Relevant interested parties identified | Record | No |
| 2 | Relevant requirements of each party determined | Analysis or register | No |
| 3 | Requirements monitored and reviewed | Review record | No |
| 4 | Legal/regulatory interested parties included | Register | No |

---

## Clause 5.1 — Leadership and Commitment

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | QMS requirements integrated into business processes | Evidence of integration | No |
| 2 | Policy established and communicated | Policy + communication evidence | No |
| 3 | Resources provided | Resource allocation record | No |
| 4 | Customer focus (5.1.2) — customer/statutory/regulatory requirements met | Evidence | No |
| 5 | Quality culture and ethical behaviour promoted (2026) | Observable practice, interview, communication | No |
| 6 | Management review conducted | MR minutes | No |

---

## Clause 6.1 — Actions to Address Risks and Opportunities

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Risks and opportunities determined (separate from objectives) | Risk register or analysis | No |
| 2 | Actions planned for risks and opportunities | Action plan | No |
| 3 | Actions integrated into QMS processes | Process documentation | No |
| 4 | Effectiveness of actions evaluated | Evaluation record | No |
| 5 | Risks and opportunities separately addressed (2026 — no longer combined R&O planning) | Distinct records | No |

**2026 change:** Risks and opportunities must be separately documented, not merged.
**Major M4:** No risk/opportunity planning process at all.

---

## Clause 6.2 — Quality Objectives

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Objectives established at relevant functions | Documented objectives | No |
| 2 | Measurable (where practicable) | Metrics or rationale | **`where practicable`** |
| 3 | Consistent with quality policy | Linkage evidence | No |
| 4 | Relevant to product/service conformity | Objectives linked to products/processes | No |
| 5 | What will be done, by whom, by when, with what resources | Action plan | No |
| 6 | How results evaluated | Evaluation records | No |

---

## Clause 6.3 — Planning of Changes

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Changes carried out in a planned manner | Change request or controlled record | No |
| 2 | Purpose and consequences considered | Change review record | No |
| 3 | QMS integrity maintained | Post-change review | No |
| 4 | Resource availability confirmed | Resource check record | No |
| 5 | Responsibility and authority confirmed | Assignment record | No |

**Major M1/M3:** Change implemented affecting product/service conformity without any planning.

---

## Clause 7.1.5 — Monitoring and Measuring Resources

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Resources determined | Monitoring plan or equipment register | No |
| 2 | Resources are suitable | Calibration/verification evidence | No |
| 3 | Resources maintained for fitness for purpose | Maintenance records | No |
| 4 | Calibration/verification traceable to standards (when required) | Calibration certificate | **by circumstance** — 7.1.5.2 lead-in “when traceability … is a requirement or is considered essential” (no `as appropriate` in the text) |
| 5 | Calibration status identified | Labels, records | **by circumstance** — same 7.1.5.2 lead-in (no `as appropriate` in the text) |
| 6 | Safeguarded from adjustments, damage, deterioration | Control records | No |
| 7 | Out-of-tolerance impact assessed | Assessment record | **`as necessary`** (7.1.5.2: appropriate action as necessary) |

**Conditional (element 4):** If equipment NOT used for release or critical measurements and rationale documented → OFI.
**Major M3:** Equipment used for release decision, calibration record absent.

---

## Clause 7.2 — Competence

| # | Element | Evidence type |
|---|---|---|
| 1 | Competence requirements determined | Matrix, JD, or procedure |
| 2 | Persons are competent (education, training, experience) | Records or credentials |
| 3 | Actions taken where gaps identified | Training plan + records |
| 4 | Effectiveness of actions evaluated | Assessment or result record |
| 5 | Retained documented information as evidence | Training records |

**Implementation heavy:** Policy/procedure alone insufficient — training records and competence evidence required.

---

## Clause 7.3 — Awareness

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Awareness of quality policy | Communication records or interview | No |
| 2 | Awareness of relevant objectives | Records or interview | No |
| 3 | Awareness of their contribution to QMS effectiveness | Records or interview | No |
| 4 | Implications of nonconformity communicated | Communication records | No |

---

## Clause 7.4 — Communication

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Internal communication processes established | Communication plan or records | No |
| 2 | External communication (what, when, with whom, how) | Process documentation | No |
| 3 | Quality culture communication (2026) | Observable channels | No |

---

## Clause 7.5 — Documented Information

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Required documented information maintained | Document register | No |
| 2 | Documents controlled (creation, update, access, distribution) | Control records | **`as applicable`** (7.5.3.2 lead-in) |
| 3 | External origin documents identified and controlled | Register | **`as appropriate`** (7.5.3.2) |
| 4 | Documents protected from unintended alteration or loss | System or physical controls | No |
| 5 | Obsolete documents controlled | Disposition records | No |

---

## Clause 8.1 — Operational Planning and Control

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Processes established for product/service delivery | Documented processes | No |
| 2 | Criteria for processes defined | Documented criteria | No |
| 3 | Controls implemented and records retained | Operational records | No |
| 4 | Planned changes controlled | Change records | No |
| 5 | Outsourced processes controlled | Supplier/outsourcing control evidence | No |

---

## Clause 8.3 — Design and Development (CONDITIONAL — by scope, 4.3 / Annex A.3)

**Conditionality:** the 8.3.x text contains **no** `where applicable` phrase (the phrases that do occur are 8.3.5 `as appropriate` and 8.3.6 `to the extent necessary`). D&D can fall outside the QMS only through the 4.3 scope determination, valid only if it does not affect conformity, customer satisfaction or statutory/regulatory obligations (Annex A.3). If organization assessed D&D as not applicable with documented rationale → OFI at most. If D&D clearly applies (product/service design): entire process required.
> *Flag (2026-10-06):* the “OFI at most” sentence above predates the L7 wording in `SKILL.md` / ref 26, which returns **Complied** for a justified not-applicable. The two are not reconciled here — pending the gate review noted in `docs/eei-blueprint-crosswalk.md`.

| # | Element | Evidence type |
|---|---|---|
| 1 | D&D planning inputs determined | Design inputs record |
| 2 | Requirements determined (functional, performance, regulatory) | Requirements specification |
| 3 | Interface between functions managed | Interface record or meeting minutes |
| 4 | Design outputs meet input requirements | D&D output review record |
| 5 | Design reviews conducted at appropriate stages | Review records |
| 6 | Design verification conducted | Verification records |
| 7 | Design validation conducted | Validation records |
| 8 | Changes controlled and documented | Change control records |
| 9 | Design outputs released per authorization | Release authorization record |

**Major M4:** D&D applicable but entire process absent.
**Major M3:** Unverified or unvalidated design released.

---

## Clause 8.4 — Control of Externally Provided Processes, Products, Services

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Type and extent of control determined for each supplier | Supplier control plan | No |
| 2 | Criteria for supplier evaluation established | Evaluation criteria document | No |
| 3 | Suppliers evaluated before use | Evaluation records | No |
| 4 | Suppliers re-evaluated periodically | Re-evaluation records | No |
| 5 | Requirements communicated to suppliers | PO, specification, contract | **`as appropriate`** (8.4.3) |
| 6 | Verification activities for externally provided items | Inspection/acceptance records | **by circumstance** — 8.4.2 “activities necessary to ensure…” (no `as appropriate` in the text) |
| 7 | Approved supplier list maintained | ASL or register | No |

**Major M4:** No supplier evaluation or control process for any supplier.
**Major M1:** Critical supplier (affecting product conformity) not evaluated or controlled.

---

## Clause 8.5 — Production and Service Provision

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | Controlled conditions — documented information available | Procedures, WIs | No |
| 2 | Controlled conditions — suitable monitoring/measuring resources | Equipment records | No |
| 3 | Controlled conditions — competent persons | Competence records | No |
| 4 | Controlled conditions — infrastructure | Maintenance records | No |
| 5 | Unique identification and traceability | Traceability records | **`when it is necessary`** (8.5.2; unique identification also under a “when traceability is a requirement” condition) |
| 6 | Customer/external property identified, protected, reported | Records | **by circumstance** — only when such property exists (8.5.3 has no qualifier phrase) |
| 7 | Preservation of outputs | Preservation records | **`to the extent necessary`** (8.5.4) |
| 8 | Post-delivery activities | Activity records | **by circumstance** — only where post-delivery activities exist (8.5.5 has no qualifier phrase) |
| 9 | Control of changes | Change control records | No |

---

## Clause 8.6 — Release of Products and Services

| # | Element | Evidence type |
|---|---|---|
| 1 | Planned arrangements for release completed | Release checklist or procedure |
| 2 | Acceptance criteria met with objective evidence | Inspection/test records |
| 3 | Release authorization traceable to authorized person | Signed release record |
| 4 | Documentation retained showing product/service conformity | Records |
| 5 | Person(s) authorizing release identified | Authorized signatory records |

**Implementation heavy — procedure alone insufficient.**
**All 5 elements are mandatory for releases.** Missing element 1–3 → Major M3.

---

## Clause 8.7 — Control of Nonconforming Outputs

| # | Element | Evidence type |
|---|---|---|
| 1 | Nonconforming outputs identified | NC record or tag |
| 2 | Nonconforming outputs controlled (prevent unintended use/delivery) | Quarantine/segregation records |
| 3 | Disposition determined: correction / concession / rejection / hold | Disposition record |
| 4 | Authorization for concession where required | Authorized concession record |
| 5 | Re-verification after correction | Re-inspection/test record |
| 6 | Information retained | Records |
| 7 | Customer notification when nonconforming output delivered | Notification record |

**Major M3:** NC output delivered to customer without authorization or without elements 3–4.
**Major M4:** No NC output control process at all.

---

## Clause 9.1 — Monitoring, Measurement, Analysis and Evaluation

| # | Element | Evidence type | Conditional? |
|---|---|---|---|
| 1 | What is monitored and measured determined | Monitoring plan | No |
| 2 | Methods valid and reliable | Documented methods | No |
| 3 | When and by whom performed | Schedule / assignment | No |
| 4 | Results analyzed and evaluated | Analysis records | No |
| 5 | Customer satisfaction monitored | Survey, feedback, complaint data | No |
| 6 | Results communicated | Report or management review input | No |

---

## Clause 9.2 — Internal Audit

| # | Element | Evidence type |
|---|---|---|
| 1 | Audit programme established | Programme document |
| 2 | Programme considers importance of processes and previous audit results | Programme rationale |
| 3 | Audit criteria, scope, frequency, methods defined | Programme |
| 4 | Audits conducted at planned intervals | Audit reports |
| 5 | Auditor objectivity and impartiality ensured | Assignment/independence record |
| 6 | Results reported to management | Report routing evidence |
| 7 | Corrective actions taken without undue delay | CA records |
| 8 | Retained documented information | Audit records |

**Implementation heavy.**
**Major M4:** No internal audit programme at all.
**Major M5:** Previous NCs excluded from follow-up or programme unchanged after repeated failures.

---

## Clause 9.3 — Management Review

| # | Element | Evidence type |
|---|---|---|
| 1 | Review conducted at planned intervals | Review record / minutes |
| 2 | Status of actions from previous reviews (input) | Previous action tracking |
| 3 | Changes in external/internal issues (input) | Documented consideration |
| 4 | Information on QMS performance (input) — customer satisfaction, process performance, NC/CA status, audit results, supplier performance | Data/metrics |
| 5 | Resource adequacy (input) | Resource section in MR |
| 6 | Risks and opportunities (input) | R&O update |
| 7 | Output decisions on opportunities for improvement | Documented decisions |
| 8 | Output decisions on QMS changes | Documented decisions |
| 9 | Output decisions on resources needed | Documented decisions |
| 10 | Retained documented information as evidence | MR minutes |

**Major M4:** No management review conducted.
**Minor D2:** Review conducted but 1–2 required inputs absent.

---

## Clause 10.2 — Nonconformity and Corrective Action

| # | Element | Evidence type |
|---|---|---|
| 1 | Reaction to NC (containment, correction) | NC record + correction evidence |
| 2 | Root cause analysis conducted | RCA record |
| 3 | Corrective action determined and implemented | CA plan + implementation evidence |
| 4 | Effectiveness of CA reviewed | Effectiveness review record |
| 5 | QMS updated if needed | Change records |
| 6 | Risks identified as a result of NC | Updated risk register |
| 7 | Retained documented information | CA records |

**All 7 elements mandatory for material NCs.**
**Major M5:** Same NC recurred after element 4 confirmed effective.
**Minor D2:** Elements 2–4 present but one incomplete; no recurrence.
