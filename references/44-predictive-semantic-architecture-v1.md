# QMS Predictive Semantic Architecture v1

## Purpose
Add a non-authoritative predictive intelligence layer upstream of the existing AIAS deterministic assurance engine.

## Non-negotiable authority rule
- Predictive output is **not audit evidence**.
- Embedding similarity is **not proof of conformity or nonconformity**.
- A predicted missing state is only an investigation candidate.
- Only the existing evidence-gated state machine and human-auditor release path may produce a material audit conclusion.

## Research-derived design basis
This module adapts two non-normative machine-learning ideas into structured QMS audit reasoning:
1. Joint-Embedding Predictive Architecture (JEPA): predict abstract target representations from informative context rather than reconstructing missing raw input.
2. World-model / imagination training: represent sequential state transitions and evaluate candidate actions before real interaction.

These ideas are enabling architecture only. They must never be cited as ISO 9001 requirements or certification criteria.

## vNext cognitive split
1. **Knowledge Engine** — controlled ISO requirements, clause profiles, atomic obligations.
2. **Semantic Engine** — encode what evidence means in the context of a process and requirement.
3. **Predictive Engine** — identify candidate missing states, contradictions, and expected evidence classes.
4. **Audit Policy Engine** — rank next-best audit actions.
5. **Assurance Engine** — deterministic state machine, gates, severity anchors, grounding, human review.

## Required invariant
`PREDICT -> INVESTIGATE -> VERIFY -> GATE -> CONCLUDE`

Forbidden shortcut:
`PREDICT -> CONCLUDE`

## Output labels
Every predictive artifact must carry:
```json
{
  "epistemic_class": "prediction_only",
  "evidence_status": "not_audit_evidence",
  "release_authority": "none"
}
```
