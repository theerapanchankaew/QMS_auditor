# AIAS Process Enforcer Binding v1

## Purpose
Bind predictive intelligence to the existing deterministic 12-state AIAS decision machine. The Process Enforcer is the assurance boundary; predictive modules are upstream advisory modules.

## Authoritative state sequence
`S0 RECEIVED -> S1 PREFLIGHT -> S2 NORMALIZED -> S3 MAPPED -> S4 SUFFICIENCY -> S5 BREACH_TEST -> S6 EXPOSURE -> S7 SEVERITY -> S8 GROUNDING -> S9 HUMAN_REVIEW -> S10 RELEASED -> S11 MONITORED`

## Binding rules
- Predictive modules may operate only between S3 and S4 as investigation support, or during S11 for controlled learning analysis.
- A predictive module may propose transition candidates but cannot mutate the authoritative state-machine state.
- Only observed evidence can advance sufficiency and breach gates.
- Any `prediction_only` artifact entering a material decision basis must trigger PE-1 and be excluded from proof fields.
- S8 grounding must verify citations/provenance before S9.
- S9 human review is mandatory before S10 release for material certification findings.

## Fail closed
If state lineage, evidence provenance, or simulation/evidence separation is ambiguous, route to `ReviewRequired` or `InsufficientEvidence`; never infer a pass condition.
