# AWM v0.7 Perception, Provenance and Temporal Contract

## Purpose
Control how external audit material becomes machine-usable evidence and how time-dependent world state is reconstructed.

## Evidence promotion
Maintain the separation `RAW -> CANDIDATE -> PRESENTED -> CORROBORATED/VERIFIED`. Retrieval never equals verification. A retrieved span must retain source id, version, page/record locator, source hash, and span hash.

## Perception components
The bundled runtime supports PDF, DOCX, XLSX and text ingestion through deterministic parsers and normalizes them to source spans and evidence candidates. Use the runtime contracts rather than free-form LLM extraction whenever programmatic execution is available.

## Temporal model
Track both valid time (when a fact is true in the organization) and transaction time (when AIAS learned/recorded it). Reconstruct audit state as-of the audit date and knowledge cut-off. Never use late-arriving evidence to rewrite what the auditor could have known at the earlier time.

## Recurrence
Recurrence detection is an upstream signal only. M5 eligibility requires the existing Major escalation logic and human review. Do not convert temporal similarity alone into Major NC.
