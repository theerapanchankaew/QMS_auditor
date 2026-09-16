# Local RAG Governance for Closed QMS Auditor Skill

This skill may use local RAG only as a controlled evidence repository, never as an open search tool.

## Non-negotiable rules

1. Do not use web fallback, external connectors, public websites, or model memory for audit substance.
2. Use local RAG only when the RAG profile is approved in `assets/manifests/local-rag-connection-policy.json`.
3. Use only source IDs registered in `assets/manifests/bundled-source-manifest.json` or user-uploaded controlled evidence for the current task.
4. Every retrieved chunk must carry source trace: `source_id`, document title, controlled location, page/section/chunk where available, and checksum when available.
5. If the local RAG profile, index, or source trace is missing, return `ReferenceGap` or `ReviewRequired`; do not improvise.
6. All outputs must follow the human auditor logic contract.

## Approved modes

- `bundled_only`: use only bundled `references/**` and `assets/**`.
- `uploaded_controlled_evidence`: use a user-uploaded document only for the current task after declaring it controlled evidence.
- `approved_local_rag`: use a local index that is declared in the local RAG policy and derived from manifest sources.

Forbidden modes: `web`, `online`, `latest`, `auto_update`, `external_search`, `connector_search`.

## Fail-closed behavior

When the requested term, clause, or evidence cannot be found, answer with `ReferenceGap` in the human auditor frame and ask the user to upload or register a controlled source. Do not search elsewhere.
