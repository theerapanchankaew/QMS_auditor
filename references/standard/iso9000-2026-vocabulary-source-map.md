# ISO 9000 Vocabulary Source Map

> **Status (2026-10-05):** the ISO 9000 sources named here are listed under `unavailable_historical_sources` in `assets/manifests/bundled-source-manifest.json` and are not part of the active retrieval/RAG boundary. Use them only if the user supplies them as controlled evidence for the current task; otherwise return `ReferenceGap` for terminology that needs them.

This skill includes controlled, bundled vocabulary sources for ISO 9000 family terminology. Use these local sources only. Do not search web, ISO OBP, connector stores, or external websites for definitions.

## Bundled sources

| Source | Path | Use |
|---|---|---|
| ISO/FDIS 9000:2026 fundamentals and vocabulary | `assets/standards/ISO_FDIS_9000_2026_en.pdf` | Formal terms, definitions, notes, concept relationships, and quality management fundamentals |
| ISO 9000 Glossary 2025 | `assets/standards/ISO9000GlossaryENv5FA2025.pdf` | Selected common-word meanings used in ISO 9000/ISO 9001 family documents |
| Definition navigation index | `references/standard/iso9001-2026-definition-index.md` | Fast local lookup and synonym redirects for frequent terms |

## Mandatory lookup route

1. Run `python scripts/closed_source_entrypoint.py --request "<term/question>" --planned-action "Searching bundled skill sources for the requested ISO/QMS term" --resolve`.
2. Use returned local traces from `references/**` or `assets/standards/**`.
3. If the entrypoint returns `ReferenceGap`, do not search the web. Ask the user to upload the authoritative source as controlled evidence.

## Known synonym / typo redirects

| User wording | Controlled term |
|---|---|
| dispute recovery provider | DRP-provider / dispute resolution process provider |
| recovery provider | dispute resolution process provider |
| DRP provider | DRP-provider |

## DRP-provider audit interpretation note

For a certification or complaints-handling system, a DRP-provider is relevant when complaints can become disputes requiring an external dispute resolution process. Audit interpretation should focus on whether the organization has defined when unresolved complaints escalate, who is independent/impartial, how records are controlled, and how customer feedback/dispute outcomes are used for improvement. Do not infer legal obligations unless the user supplies the legal or scheme requirement as a controlled source.
