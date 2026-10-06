# ISO 9001:2026 Definition Index

Use this file for quick navigation to terms. For exact definitions, run `scripts/extract_clause.py 3` or `scripts/search_standard.py "<term>"` against the full PDF.

## Core terms included in clause 3
- **3.1 organization**: entity within QMS scope, including part of a larger entity.
- **3.2 interested party / stakeholder**: person or organization that can affect, be affected by, or perceive itself to be affected by a decision/activity.
- **3.3 top management**: person/group directing and controlling the organization at the highest level.
- **3.4 management system** and **3.4.1 quality management system**: interrelated/interacting elements related to policy, objectives and processes; QMS is the quality-related part of the overall management system.
- **3.5 policy** and **3.5.1 quality policy**: intentions and direction formally expressed by top management; quality policy relates to quality.
- **3.6 objective** and **3.6.1 quality objective**: result to be achieved; quality objective relates to quality.
- **3.7 risk**: effect of uncertainty.
- **3.8 process**: interrelated/interacting activities using or transforming inputs to deliver a result.
- **3.9 competence**: ability to apply knowledge and skills to achieve intended results.
- **3.10 documented information**: controlled and maintained information and its medium.
- **3.11 performance**: measurable result.
- **3.12 continual improvement**: recurring activity to enhance performance.
- **3.13 effectiveness**: extent to which planned activities are realized and planned results achieved.
- **3.14 requirement**: need or expectation that is stated, generally implied, or obligatory.
- **3.15 conformity**: fulfilment of a requirement.
- **3.16 nonconformity**: non-fulfilment of a requirement.
- **3.17 corrective action**: action to eliminate cause(s) of a nonconformity and prevent recurrence.
- **3.18 audit**: systematic and independent process for obtaining evidence and evaluating it objectively against audit criteria.
- **3.19 measurement**: process to determine a value.
- **3.20 monitoring**: determining the status of a system, process, or activity.

## Clarification terms from Annex A
Annex A.2 clarifies words that often affect audit interpretation (paraphrased; use the registered PDF for the exact text):
- **appropriate vs applicable** — not interchangeable. *Appropriate*: suitable for the organization's context, involving judgement about what meets the requirement. *Applicable*: if the requirement is determined to be relevant or possible, it applies to the organization. *As applicable*: a requirement that is generally applicable under 4.3 may be determined not applicable in some situations.
- **not applicable (A.3)** — allowed only if this does not affect the organization's ability to ensure conformity of products and services, enhance customer satisfaction or fulfil applicable statutory and regulatory obligations; it reflects that the organization considered the requirement and determined, with justification, that it does not apply in its context (see 4.3).
- **consider vs take into account** — *consider*: think about whether the topic will be included in decisions or actions; *take into account*: think about it and include it in decisions or actions.
- **continual vs continuous** — *continual*: over a period of time with intervals of interruption (the word used for improvement); *continuous* (not used in the document): without interruption.
- **ensure** — a responsibility for making a specified result exist or occur; it is accountability for the result, not performing every activity directly (actions can be delegated).
- **shall be available as documented information vs documented information shall be available as evidence of** — the first concerns availability of information obtained, used or provided by the organization; the second concerns retention of objective evidence (and does not imply legal evidential requirements).
- **strategic direction** — coordinated decisions, plans and actions that guide the organization towards its objectives.

Where these terms appear as conditional qualifiers in clauses 4–10, see `iso9001-2026-standard-map.md` → “Conditional qualifiers in clauses 4–10”.

Use Annex A as informative clarification only; do not treat it as adding requirements.

## ISO 9000:2026 vocabulary source additions

> **Status (2026-10-05):** the ISO 9000 sources named here are listed under `unavailable_historical_sources` in `assets/manifests/bundled-source-manifest.json` and are not part of the active retrieval/RAG boundary. Use them only if the user supplies them as controlled evidence for the current task; otherwise return `ReferenceGap` for terminology that needs them.

The bundled vocabulary source `assets/standards/ISO_FDIS_9000_2026_en.pdf` is allowed for ISO 9000 family definitions and term relationships. Use it before returning `ReferenceGap` for terminology questions.

- **3.1.11 DRP-provider / dispute resolution process provider**: person or organization that supplies and operates an external dispute resolution process. Common user typo/alias: “dispute recovery provider”. For audit dialogue, map the typo to DRP-provider and cite the bundled ISO 9000 source trace rather than searching outside.
- **3.9.4 dispute**: disagreement arising from a complaint and submitted to a DRP-provider.
- **3.9.5 dispute resolver**: individual assigned by a DRP-provider to help parties resolve a dispute.
- **3.9.6 complainant**: person, organization, or representative making a complaint.

The ISO 9000 Glossary file `assets/standards/ISO9000GlossaryENv5FA2025.pdf` is also bundled as an allowed support source for selected common-word meanings in the ISO 9000 family. Use it only as glossary guidance, not as a substitute for formal terms and definitions in ISO 9000/ISO 9001.
