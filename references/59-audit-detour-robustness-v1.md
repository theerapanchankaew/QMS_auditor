# AIAS Audit Detour Robustness v1

## Purpose
Evaluate whether the Audit World Model remains coherent when the audit trajectory is perturbed by a valid but unexpected event.

## Detour operators
Apply one material perturbation at a time:
- remove an expected record;
- introduce a contradictory interview;
- mark evidence stale;
- change applicability;
- expand or narrow the sample;
- reveal previously missing objective evidence;
- introduce a corrective-action record;
- change systemicity from local to organization-wide or vice versa;
- replace an intended audit action with another valid action.

## Required behavior
After a detour, AIAS must:
1. update only affected state variables;
2. preserve unrelated verified facts;
3. re-evaluate valid next actions;
4. reverse prior planning assumptions when necessary;
5. never convert the detour itself into a finding;
6. never skip deterministic gates;
7. route to human review when the perturbation creates unresolved conflict.

## Metrics
- valid continuation rate after detour;
- state-delta accuracy;
- recovery-to-coherent-state rate;
- forbidden-transition rate;
- unsupported-verdict rate (target 0);
- perturbation sensitivity by detour class.

## Adversarial detours
Include legal but low-ranked or inconvenient audit actions. The objective is to test whether the model learned the domain structure rather than only common audit paths.
