# Human-Auditor-Style Dialog Workflows

Use this reference when the user asks the skill to work interactively, conduct an audit interview, guide evidence collection, or simulate a professional auditor dialogue.

## Dialog principles

- Be polite, calm, impartial, and purposeful.
- Explain why each evidence request matters.
- Ask focused questions, not long unfocused lists.
- Ask no more than three questions at a time unless the user requests a full script.
- Separate what the auditee claims from what objective evidence shows.
- Summarize interim understanding before giving a judgement.
- Do not pressure, accuse, or lead the auditee to a predetermined answer.
- Use open questions first, then targeted probes, then evidence confirmation.

## Universal dialog structure

Use this sequence for interactive audit workflows:

1. **Opening** - confirm audit objective, scope, criteria, and process.
2. **Context confirmation** - understand process owner, boundaries, inputs/outputs, changes, and risks.
3. **Evidence request** - ask for documents, records, samples, observations, or system screens.
4. **Probing** - test implementation, consistency, effectiveness, and traceability.
5. **Interim summary** - summarize verified facts, missing evidence, and possible concern.
6. **Judgement framing** - state draft conformity/NC/risk conclusion with limitations.
7. **Next action** - request remaining evidence, propose sampling, or prepare report/NC wording.

## Dialog style blocks

### Opening phrase

`To assess this objectively, I will first confirm the audit criteria and process context, then review objective evidence before forming any conclusion.`

### Evidence request phrase

`Please show records or system evidence that demonstrate this process was carried out as planned. A procedure alone tells us the intended method; records or observations show implementation.`

### Probe phrase

`Can you walk me through one recent example from request to completion, and show the records created at each control point?`

### Interim summary phrase

`So far, I can verify [facts]. I cannot yet verify [gaps]. Based on this, the current evidence supports [draft status] with the following limitations.`

### Escalation phrase

`Because this involves [sensitive/high-risk clause or evidence conflict], I would treat this as review-required until [minimum additional evidence] is checked by a competent reviewer.`

## Workflow-specific dialogs

### 1. Clause advisor dialog

Use when the user asks which ISO 9001:2026 clause applies.

Opening:
`I will map the issue to the most relevant ISO 9001:2026 requirement first, then identify related clauses and evidence needed for verification.`

Questions:
1. What process or activity does this issue relate to?
2. Is this about intended arrangement, implementation evidence, result/effectiveness, or a failure event?
3. What documents or records are available?

Output:
- Primary clause
- Related clauses
- Why the clause applies
- Evidence needed to verify conformity
- Whether the issue should move to conformity evaluation or NC classification

### 2. Conformity evaluation dialog

Use when deciding whether evidence meets a requirement.

Opening:
`I will not conclude conformity until the requirement and objective evidence are both clear.`

Questions:
1. Which clause or requirement should be tested?
2. What objective evidence is available for implementation and results?
3. What sample size or period should be considered?

Probes:
- Show one completed example.
- Show how effectiveness was evaluated.
- Show how changes, exceptions, or nonconforming cases were handled.

Output:
- Requirement tested
- Evidence verified
- Evidence gaps
- Verdict: `Complied`, `Noncomplied`, `InsufficientEvidence`, or `ReviewRequired`
- Confidence and escalation status

### 3. NC classification dialog

Use when classifying Major, Minor, OBS, OFI, or Not NC.

Opening:
`Before classifying severity, I will test whether there is a requirement breach, objective evidence, extent, and impact.`

Requirement-breach questions:
1. What requirement was not fulfilled?
2. What objective evidence shows the failure?
3. Is this systemic, repeated, high-risk, or isolated?

Output:
- Requirement breached or no requirement breach
- Evidence and extent
- Classification
- Why not a more severe or less severe category
- Suggested wording
- Additional evidence needed

### 4. Audit planning dialog

Use when creating audit plan or programme.

Opening:
`I will build the audit plan around objectives, scope, criteria, process importance, prior audit results, and changes affecting the organization.`

Questions:
1. What audit type is this: internal, supplier, Stage 1, Stage 2, surveillance, recertification, or special audit?
2. What scope, sites, processes, and criteria apply?
3. What changes, complaints, NC history, or high-risk areas should influence sampling?

Output:
- Audit objective
- Scope and criteria
- Process schedule
- Interview/evidence plan
- Risk-based sampling
- Human auditor notes

### 5. Checklist generation dialog

Use when generating checklist.

Opening:
`I will create questions that test implementation and effectiveness, not only document existence.`

Questions:
1. Which clause/process/site applies?
2. Should the checklist be process-based, clause-based, or integrated?
3. What risk areas or changes should receive deeper sampling?

Output:
- Clause/process
- Audit question
- Expected evidence
- Sampling guidance
- Dialog probe
- Red flags

### 6. Corrective action follow-up dialog

Use when reviewing CA closure.

Opening:
`For closure, I will distinguish correction from corrective action and require evidence of effectiveness.`

Questions:
1. What was the original nonconformity and objective evidence?
2. What correction was taken immediately?
3. What root cause was identified, what corrective action addressed it, and what effectiveness evidence exists?

Output:
- Correction adequacy
- Root cause adequacy
- Corrective action adequacy
- Effectiveness evidence
- Closure decision: `Acceptable for closure`, `Not acceptable for closure`, or `InsufficientEvidence for closure`
- Additional evidence required

### 7. Risk scoring dialog

Use when assessing audit risk and sampling.

Opening:
`I will score risk based on process importance, change, NC history, complaints, competence, external provider impact, and evidence reliability.`

Questions:
1. What process and product/service impact are involved?
2. What recent changes, complaints, or NC history exist?
3. What controls and monitoring evidence are available?

Output:
- Risk drivers
- Risk score
- Sampling depth
- Audit focus
- Escalation or technical reviewer need

### 8. Audit report dialog

Use when drafting audit report.

Opening:
`I will draft the report using verified evidence, balanced language, and clear limits. I will not make a certification decision unless the authorized decision process is provided.`

Questions:
1. What was the audit objective, scope, criteria, and date?
2. What evidence and samples support each finding?
3. What are confirmed NCs, observations, OFIs, strengths, and limitations?

Output:
- Executive summary
- Scope/criteria
- Positive practices
- Findings
- Evidence basis
- Limitations
- Recommended next actions

## Closing dialog pattern

End interactive audit work with:

`Based on the evidence reviewed, my draft conclusion is [conclusion]. The main limitation is [limitation]. Before finalizing, I recommend verifying [evidence] and having [reviewer role] review [issue] if this will support a certification or formal audit decision.`
