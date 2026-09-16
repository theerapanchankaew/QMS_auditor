# Scope Detection Rules

## Purpose
Detect requests that are out of scope for this skill before consuming any audit resources. The scope gate runs first — before the preflight guard, before route selection, before any clause lookup.

## Permitted scope (in scope)

All of the following are in scope:

- ISO 9001:2026 clause interpretation, audit planning, evidence evaluation, finding classification
- ISO 9001:2015 transition support and gap analysis
- ISO 9001 conformity evaluation, corrective action review, audit report drafting
- ISO 9000:2026 vocabulary and term clarification
- QMS process analysis, risk and opportunity assessment, planning of changes
- Management system certification questions (Stage 1 / Stage 2 / surveillance / recertification)
- AHP-based QMS readiness or audit prioritization
- Related management system dialogue that cross-references ISO 9001 requirements (e.g. AS9100, IATF 16949 alignment questions that invoke ISO 9001 clauses)

## Out-of-scope categories and responses

### Category A — Wrong standard
- Requests about ISO/IEC 27001, 27017, 27018, ISO 45001, ISO 14001, ISO 56001, ISO 13485, IATF 16949 (standalone, not cross-referencing ISO 9001), GMP, FDA, CE marking without QMS context.
- Response: `OUT_OF_SCOPE_WRONG_STANDARD` — state which standard the user needs and suggest an appropriate skill or resource.

### Category B — General knowledge / research
- Requests for general business strategy, HR advice, legal interpretation, financial analysis, market research, or industry benchmarks not tied to a QMS clause or audit task.
- Response: `OUT_OF_SCOPE_GENERAL_KNOWLEDGE`

### Category C — Certification body / accreditation authority decisions
- Requests asking this skill to decide on certification issuance, accreditation status, or to override a certification body decision.
- Response: `OUT_OF_SCOPE_CB_DECISION` — clarify that only accredited CBs can make certification decisions; this skill supports audit reasoning, not certification authority.

### Category D — Personal legal, medical, or financial advice
- Response: `OUT_OF_SCOPE_PERSONAL_ADVICE`

### Category E — Ambiguous scope
- The request could be in scope with minor clarification (e.g. "help me with my quality system" without specifying the standard).
- Response: Ask one scoping question before refusing. Example: "ขอให้ระบุมาตรฐานที่ใช้เป็น audit criterion ก่อนครับ — ใช้ ISO 9001 หรือมาตรฐานอื่น?"

## Scope dialog template

**Out-of-scope response structure:**
```
[SCOPE_GATE] status: OUT_OF_SCOPE
category: <A|B|C|D>
request_summary: <one-line summary>
reason_th: <ภาษาไทย — อธิบายสั้นๆ ว่าอยู่นอก scope ของ skill นี้>
suggestion_th: <แนะนำว่าควรไปที่ไหนหรือ upload อะไรเพื่อให้อยู่ใน scope>
verdict: OUT_OF_SCOPE
```

## Boundary cases

| Request | Decision |
|---|---|
| "ช่วยเปรียบ ISO 9001 กับ ISO 27001 ด้านการ document control" | IN SCOPE — comparative clause advisor |
| "อยากรู้เรื่อง PDPA" | OUT_OF_SCOPE_WRONG_STANDARD |
| "ช่วย draft audit checklist สำหรับ ISO 14001" | OUT_OF_SCOPE_WRONG_STANDARD |
| "อธิบาย clause 4.1 ให้หน่อย" | IN SCOPE — assume ISO 9001 unless contradicted |
| "ทำ risk assessment ให้โรงงานผลิตยา" | AMBIGUOUS — ask whether under ISO 9001 QMS or other framework |
| "วิเคราะห์หุ้น" | OUT_OF_SCOPE_PERSONAL_ADVICE |

## Integration with SKILL.md

The scope gate is step zero in the main workflow. It runs before the preflight guard and before any closed-source boundary check. If the scope gate returns `OUT_OF_SCOPE`, do not proceed further. If the scope gate returns `AMBIGUOUS`, ask one question and wait.

Add this to the mandatory runtime sequence:

```
SCOPE_GATE → PREFLIGHT_GUARD → CONFIRMATION_GATE → ROUTE → OUTPUT → FEEDBACK
```
