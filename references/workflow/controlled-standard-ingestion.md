# Controlled Standard Ingestion Workflow

Use this workflow when a new standard, guideline, manual, procedure, or controlled evidence document should become part of the skill bundle or local controlled source set.

## Steps

1. Receive the file from the user as controlled evidence.
2. Confirm metadata:
   - title
   - standard number or document code
   - edition/version/effective date
   - language
   - status: draft, final, guidance, internal procedure, regulation, or evidence record
   - allowed use: definition lookup, clause interpretation, audit evaluation, certification impact, or training
3. Register the source in `assets/manifests/bundled-source-manifest.json` or a task-specific controlled evidence manifest.
4. Validate location, checksum, source ID uniqueness, and prohibited external fields.
5. Build or refresh indexes using `scripts/standard_index_builder.py` if needed.
6. Test retrieval through `scripts/closed_source_entrypoint.py --resolve` or `scripts/local_rag_adapter.py`.
7. Repackage the skill if the source is to be bundled permanently.

## Required dialog

Before using a newly uploaded source permanently, ask the user to confirm that it is authorized for inclusion as a controlled source and specify its permitted use. Do not treat a random upload as a new standing standard unless it is registered.
