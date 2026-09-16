# Output Templates

## Conformity Evaluation
```markdown
## Audit Question

## Applicable Requirement

## Evidence Reviewed

## Requirement Testing

## Analysis

## Verdict
- Verdict:
- Confidence:
- Rationale:

## AHP / Risk Consideration

## Missing Evidence

## Review / Escalation
```

## NC Classification
```markdown
## Finding Statement

## Clause Reference

## Classification

## Severity Rationale

## Evidence Basis

## Suggested NC Wording

## Additional Evidence Needed
```

## ISO Clause Advisor
```markdown
## Input Interpreted

## Primary Clause

## Related Clauses

## Why These Clauses Apply

## Verification Suggestions

## Evidence to Request
```

## Risk Scoring
```markdown
## Process / Area

## Risk Drivers

## Risk Score

## Sampling Recommendation

## Audit Focus

## Review Notes
```

## Audit Workflow
```markdown
## Objective

## Scope

## Criteria

## Audit Activities

## Evidence to Request

## Sampling Guidance

## Risk Focus

## Expected Deliverable
```

## Escalation Packet
```markdown
## Escalation Required

## Reason for Escalation

## Reviewer Role

## Minimum Additional Evidence

## Conflict / Ambiguity

## Recommended Next Step
```

## v2 Corrective Action Follow-Up
```markdown
## Corrective Action Review Question

## Related Requirement / Finding

## Correction Adequacy
- Decision:
- Evidence:

## Root Cause Adequacy
- Decision:
- Evidence:
- Weaknesses:

## Corrective Action Adequacy
- Decision:
- Evidence:
- Does it address the root cause?:

## Effectiveness Evidence
- Evidence reviewed:
- Recurrence check:
- Monitoring / verification:

## Closure Decision
- Acceptable for closure / Not acceptable for closure / InsufficientEvidence for closure:
- Rationale:

## Additional Evidence Required

## Review / Escalation
```

## v2 NC Wording Formula
```markdown
## Suggested NC Wording
The organization did not [required action/control], as required by [clause/procedure/criterion]. Evidence reviewed showed [record/sample/observation facts, including extent]. This indicates [clear failure statement] and may affect [risk/impact where relevant].
```

## v2 External Provider Control Evidence Request
```markdown
## Evidence to Request for External Provider Control
- Supplier selection and approval criteria
- Approved supplier list
- Initial supplier approval/evaluation records
- Planned re-evaluation records
- Supplier performance monitoring data
- Purchasing information / PO requirement communication
- Incoming verification or acceptance records
- Outsourced process controls where applicable
- Supplier NC / complaint / corrective action records where relevant
```

## v2 Escalation Packet Expanded
```markdown
## Escalation Required
Yes / No

## Trigger

## Reviewer Role

## Evidence Conflict or Ambiguity

## Minimum Additional Evidence

## Consequence if Unresolved

## Recommended Next Audit Action
```


## Human Auditor Dialog Output Add-on

When the user asks for dialog or interactive workflow, append this section to the normal output:

```markdown
## Auditor Dialogue

### Opening
[Short professional opening explaining objective, criteria, and evidence-first approach]

### Context confirmation
1. [question]
2. [question]
3. [question]

### Evidence request
1. [record/document/system evidence requested]
2. [record/document/system evidence requested]
3. [record/document/system evidence requested]

### Probing questions
1. [implementation/effectiveness probe]
2. [traceability/exception probe]
3. [change/risk/opportunity probe]

### Interim summary wording
[How the auditor summarizes verified facts and gaps]

### Next action
[Evidence to obtain, sampling to perform, or escalation/review required]
```

Keep the dialogue realistic and conversational. Do not turn it into a generic questionnaire unless the user asks for a full checklist.

## ISO 9001:2026 Transition Gap Output

```markdown
## Transition Assessment Scope

## ISO 9001:2026 Criteria Considered

## Key 2026 Themes Checked
- Climate change relevance:
- Quality culture and ethical behaviour:
- Separated risks and opportunities:
- Opportunity action effectiveness:
- Strengthened management of change:
- Organizational knowledge:
- Evidence protection / documented information:

## Evidence Reviewed

## Gaps / Insufficient Evidence

## Auditor Dialogue

## Transition Readiness Conclusion
- Status:
- Confidence:
- Review required:
```

## Corrective Action Follow-Up Output

```markdown
## Closure Review

### Correction adequacy

### Root cause adequacy

### Corrective action adequacy

### Effectiveness evidence

### Closure decision
Acceptable for closure / Not acceptable for closure / InsufficientEvidence for closure

### Additional evidence required

### Auditor dialogue for follow-up
```

## Full AHP/QMS Evaluation
```markdown
## AHP/QMS Evaluation Objective

## Full AHP Input Used
- Criteria set:
- Pairwise matrix source:
- Alternatives scored:
- Scoring scale:

## Criteria and Weights
| ID | Criterion | Clause focus | Weight | Basis |
|---|---|---|---:|---|

## Consistency Check
- lambda max:
- CI:
- RI:
- CR:
- Consistency status:

## Evidence Scoring
| Alternative | Criterion | Score | Evidence rationale | Evidence gap |
|---|---|---:|---|---|

## Weighted Result
| Alternative | Weighted score | Percent | Decision support |
|---|---:|---:|---|

## Audit Verdict Separate From Score
- Verdict:
- Confidence:
- Rationale:

## Clauses and Source Trace
- Clauses considered:
- Controlled references used:
- User evidence used:
- Evidence not provided:

## Auditor Judgement Note
AHP supports priority, evidence strictness, sampling depth, and transparent weighting. It does not prove conformity, nonconformity, or Major/Minor NC classification without clause-specific objective evidence.
```

## v3 Mandatory Human Auditor Logic Frame

Use this frame for every material answer. It can be compact, but the answer must not omit the source boundary, source/evidence basis, judgement separation, gaps, and verdict.

```markdown
## Human Auditor Frame
- Mode: human_auditor_logic
- Source boundary: bundled QMS skill sources and uploaded controlled evidence only
- External sources: not used

## Audit Objective
[What is being interpreted/tested/decided]

## Controlled Sources Used
- [Bundled reference/asset path; user evidence path if applicable]

## Source-Based Finding
[What the controlled source supports. Do not infer beyond source.]

## Thai Meaning / Auditor Explanation
[Plain Thai explanation grounded in source facts]

## Impact on Certification System
[Professional auditor judgement: effects on audit process, certification process, impartiality, complaint/appeal/dispute process, records, risk, competence, or controls]

## Evidence Gaps / Next Audit Question
[Missing evidence or up to three focused evidence questions]

## Verdict
[Informational / Complied / Noncomplied / OFI / OBS / InsufficientEvidence / ReferenceGap / ReviewRequired]
```

## v3 Controlled Source Boundary Dialog

Use when blocked or source is absent:

```markdown
## Human Auditor Frame
- Mode: human_auditor_logic
- Source boundary: bundled QMS skill sources and uploaded controlled evidence only
- External sources: not used

## Controlled Source Boundary Dialog
ผมพบว่า action นี้อาจออกนอกขอบเขต controlled source ของ QMS skill จึงไม่ค้นเว็บ ไม่ใช้ connector และไม่อ้างอิงแหล่งข้อมูลภายนอก

## Safe Next Step
1. ให้ผมค้นเฉพาะ bundled references/assets ภายใน skill
2. หากไม่พบ กรุณาอัปโหลดเอกสารทางการ/มาตรฐาน/คู่มือ/หลักฐานที่ต้องการใช้เป็น controlled evidence

## Verdict
ReferenceGap / blocked_pending_user_dialog
```
