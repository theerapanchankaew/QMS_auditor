# QMS Semantic Evidence Model v1

## Goal
Represent audit evidence at a semantic level suitable for retrieval, evidence-gap detection, contradiction analysis, and downstream state reasoning.

## Semantic state object
```json
{
  "case_id": "",
  "clause": "",
  "atomic_requirement_ids": [],
  "process": "",
  "observed_states": [],
  "expected_states": [],
  "evidence_classes": [],
  "support_relations": [],
  "contradiction_relations": [],
  "missing_state_candidates": [],
  "confidence": 0.0,
  "epistemic_class": "prediction_only"
}
```

## Atomic requirement as semantic anchor
For every mapped atomic requirement, retain:
- obligation and qualifier,
- expected implementation state,
- expected evidence classes,
- common failure modes,
- related process state,
- permitted audit actions.

Use similarity only to retrieve candidates. Final clause mapping must still satisfy the exact-clause and controlled-retrieval rules.

## Multi-target masked learning pattern
During training or synthetic evaluation, hide multiple audit-semantic targets from a complete historical case, such as:
- related atomic requirement,
- expected evidence class,
- process-control state,
- missing-evidence state,
- next audit action.

Do not train the predictive layer to reconstruct proprietary source text verbatim. Prefer target labels, structured states, embeddings, or concise normalized descriptors.

## Semantic compatibility
A semantic compatibility score can be used to surface:
- evidence supporting an obligation,
- evidence contradicting a stated control,
- evidence that is irrelevant to the mapped requirement.

Compatibility is a triage signal only. It cannot set `breach_proven=true`.
