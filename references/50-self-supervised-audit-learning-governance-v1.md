# Self-Supervised Audit Learning Governance v1

## Purpose
Enable learning from historical audit cases while preserving controlled-source, confidentiality, evidence integrity, and release governance.

## Permitted training targets
- clause/atomic-requirement representations,
- evidence classes,
- process states,
- missing-state labels,
- contradiction relations,
- next-audit-action classes.

## Prohibited learning shortcuts
- label leakage from final finding into evidence-only tasks,
- reconstructing confidential source text as the training objective,
- treating model-predicted evidence as observed evidence,
- silent online self-learning from released cases,
- automatic model promotion without regression and human approval.

## Dataset split requirements
Split by audit case or organization unit to prevent near-duplicate leakage across train/test. Preserve a locked gold benchmark for Major/Minor, IE, clause mapping, and evidence-gap boundaries.

## Release criteria for predictive modules
At minimum track:
- requirement-retrieval precision/recall,
- evidence-gap precision/recall,
- next-action top-k acceptance by auditors,
- prediction-to-evidence leakage rate (target 0),
- false Major influence rate (target 0),
- human override rate.

Predictive performance cannot override the existing certification release gates.
