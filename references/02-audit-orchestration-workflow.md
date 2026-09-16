# Audit Orchestration Workflow

## Canonical Flow
Use the AIAS-style staged reasoning model as the conceptual backbone.

`SYS -> INT -> CLR(optional) -> ROUTE -> route-specific module`

For deep conformity evaluation:

`MAP -> RET -> VER -> DEC -> ETH(optional) -> COV(always) -> ESC(optional)`

## Stages
- SYS: auditor guardrail and professional behavior. This is represented by SKILL.md and auditor behavior references.
- INT: parse raw query, documents, evidence inventory, topic keywords, and ambiguity.
- CLR: ask one clarification question if ambiguity materially affects judgement.
- ROUTE: choose the primary route.
- MAP: map issue/evidence to ISO clauses and reasoning profile.
- RET: retrieve, organize, or rank evidence. RAG is support only.
- VER: test evidence against each requirement element.
- DEC: decide verdict and confidence.
- ETH: check high-risk, sensitive, impartiality, or overclaim issues.
- COV: challenge the decision with verification questions.
- ESC: prepare human review packet when required.

## Simplification for ChatGPT Skill Use
The skill does not need to literally call separate agents. It should emulate the staged thinking internally and expose only the useful structured result to the user.

## Conditional Gates
- Clarification Gate: use when ambiguity prevents route selection or evidence evaluation.
- Ethics Gate: use for high risk, Noncomplied, sensitive clauses, potential Major NC, or competence-sensitive conclusions.
- Escalation Gate: use when review_required is true, confidence is low, evidence conflicts, or the conclusion could materially affect certification.
