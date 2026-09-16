# AWM v0.7 Runtime Integration

## Purpose
Bind the QMS Auditor skill to the executable AIAS Audit World Model v0.7 runtime without changing the authority of the existing deterministic audit kernel.

## Runtime location
`scripts/awm_runtime/` contains the executable v0.7 package. Treat it as an upstream cognitive and world-state runtime, not as a verdict authority.

## Architectural chain
`source -> perception -> provenance -> evidence candidate -> world state -> requirement state -> hypothesis -> audit action planning -> WG0-WG6 -> existing G0-G13 -> human auditor`

## Mandatory authority boundary
- Permit the world model to normalize evidence, maintain state, form hypotheses, rank audit actions, detect recurrence, and recommend additional evidence acquisition.
- Do not permit the world model or LLM to release a conformity verdict, assign Major/Minor without the existing severity gates, alter historical evidence silently, or bypass human release authority.
- Treat every model-generated world transition as proposed until validated by schema, provenance, world gates, and the deterministic harness.

## Runtime states
Use W0-W9 for world-investigation readiness and retain the existing S0-S11 controlled-decision state machine for audit verdict release. A case may enter the decision FSM only after world decision-readiness passes.

## Reproducibility
Persist source-manifest hash, rule-pack hash, model identity, prompt hash, retrieval/index version, world-snapshot hash, gate trace, and human decision. Rebuild historical state from append-only events instead of silently overwriting it.
