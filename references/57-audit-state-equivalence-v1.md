# AIAS Audit State Equivalence v1

## Purpose
Define when two different audit histories represent the same underlying audit state. Use this module before world-model coherence testing, trajectory comparison, or offline learning.

## Principle
Do not equate histories by text order. Canonicalize them by audit meaning. Two histories are state-equivalent only when all material state variables that can change a valid audit continuation are equivalent.

## Canonical state key
Build the state key from:
- criterion and clause;
- atomic requirement IDs;
- applicability and conditional qualifiers;
- verified evidence IDs/classes, freshness and provenance status;
- missing evidence classes;
- unresolved contradictions;
- process implementation/systemicity state;
- sampling scope/materiality state;
- assurance state and completed gates.

Exclude from the equivalence key:
- presentation order;
- wording style;
- auditor note ordering;
- imagined predictions;
- trajectory ID, timestamps and hashes that do not change audit meaning.

## Equivalence rule
`H1 ~= H2` only when `canonical_state(H1) == canonical_state(H2)`.

If a material field is unknown in one history and known in another, treat the states as distinct unless a deterministic rule proves the difference is immaterial.

## Safety rule
State equivalence does not prove conformity. It only says that the two histories should admit the same set of valid audit continuations under the controlled audit model.
