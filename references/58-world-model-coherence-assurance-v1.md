# AIAS World Model Coherence Assurance v1

## Purpose
Test whether AIAS behaves like a coherent audit world model rather than a shortcut classifier that maps evidence patterns directly to findings.

## Ground-truth model
Use the controlled requirement rules, evidence rules, 12-state machine, 14 gates, and process-enforcer constraints as the explicit reference automaton. Learned or generative components remain non-authoritative.

## Test family A — State compression
Create two or more distinct audit histories that canonicalize to the same AuditState. The model must admit materially equivalent continuation sets.

Measure:
- compression consistency;
- action-set Jaccard similarity;
- continuation admissibility agreement;
- forbidden-transition agreement.

A compression error occurs when equivalent states produce materially inconsistent valid continuations.

## Test family B — State distinction
Create pairs of states that differ in one material variable, such as applicability, evidence sufficiency, contradiction status, implementation proof, systemicity, or gate state. The model must preserve a valid distinguishing continuation.

Measure:
- distinction precision;
- distinction recall;
- critical-state separation rate.

A distinction error occurs when materially different states collapse into the same continuation behavior.

## Boundary-style evaluation
Do not rely only on one-step next-action accuracy. Evaluate multi-step suffixes until a meaningful difference becomes observable. Default maximum suffix depth: 5. Increase for difficult clauses.

## Release criteria
A candidate Audit World Model must pass both compression and distinction tests. High task accuracy, clause accuracy, F1, or valid next-action rate alone is insufficient evidence of world-model coherence.

## Mandatory reporting
Report at minimum:
- number of equivalent-state pairs;
- number of distinct-state pairs;
- compression consistency;
- distinction precision and recall;
- detour robustness;
- all critical failures with replayable traces.
