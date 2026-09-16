# AIAS Audit Trajectory Dataset v1

## Purpose
Define the minimum offline dataset structure for training and evaluating Audit Dynamics and Audit Policy components.

## Transition record
Each JSONL record should contain:
```json
{
  "trajectory_id": "",
  "step": 0,
  "pre_state": {},
  "action": {"action_type": "", "target": ""},
  "post_state": {},
  "observed_delta": {},
  "provenance": {},
  "audit_type": "",
  "clause": "",
  "authoritative_labels": {},
  "split_group": "case_or_client_group"
}
```

## Split rules
- Prevent client/case leakage across train, validation and test sets.
- Keep all steps from one audit case in one split.
- Maintain a dedicated detour/OOD test set.
- Maintain an equivalent-state compression set and distinct-state boundary set.

## Data quality
Reject records that mix imagined and observed evidence, omit provenance, cannot reconstruct pre/post state, or encode a final verdict as if it were an observed fact.

## Evaluation-only labels
Authoritative findings may be retained for downstream validation but must not be used to overwrite state-transition truth.
