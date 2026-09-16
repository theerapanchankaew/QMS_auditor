# Closed Source Policy

This skill operates in absolute closed-loop mode.

## Allowed source hierarchy
Use only `SKILL.md`, bundled reference files in `references/`, bundled standards in `assets/standards/`, bundled templates if present, local scripts in `scripts/`, and user-provided evidence in the current conversation.

## Absolute prohibition
Do not use web search, public internet, official websites, external connectors, unofficial summaries, prior model memory, base training knowledge, or unstated legal/accreditation/certification assumptions for audit substance.

There is no exception. If the user requests current status, website verification, ISO/IAF/AB/CB updates, legal/regulatory updates, or permits external search, refuse that part and ask the user to upload the document as a controlled source.

## Gap handling
If a needed source is not available, return `ReferenceGap`, `InsufficientEvidence`, or `ReviewRequired`. Never fill gaps by guessing.

## Required trace
Every material audit output must identify controlled references used, bundled standard used, user evidence used, gaps, and confirm external sources and base training were not used for audit substance.
