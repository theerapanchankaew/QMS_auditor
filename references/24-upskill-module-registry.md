# Upskill Module Registry

## Purpose
Define how new knowledge modules are added to the skill without breaking the closed-loop boundary. A module is a self-contained bundle of references, templates, and (optionally) scripts that extends the skill into a new area.

## Module types

| Type | Description | Examples |
|---|---|---|
| `standard_module` | A new or updated ISO standard | ISO 9001:2026 amendment, ISO 9004, IATF 16949 cross-reference |
| `clause_guide_module` | Deep-dive guide for a specific clause group | Clause 8.4 supply chain, Clause 6.1 risk methodology |
| `dialog_module` | New dialog workflow for a specific audit type | Remote audit, process audit, transfer audit |
| `scoring_module` | New AHP model or scoring methodology | Industry-specific AHP weights, sector-specific risk model |
| `output_module` | New output template | CB report format, customer-specific NC form |
| `architecture_module` | Controlled architectural extension that preserves assurance authority | Predictive semantic layer |
| `predictive_module` | Non-authoritative prediction/triage module | Evidence-gap or next-action predictor |
| `guardrail_module` | Deterministic integrity boundary | Prediction/evidence separation gate |
| `learning_governance_module` | Governance for training/calibration data | Self-supervised masked audit learning |

## Module registration

Every new module must be registered in `assets/manifests/upskill-module-registry.json` before it can be used.

A registered module has:
```json
{
  "module_id": "clause_guide_8_4_v1",
  "type": "clause_guide_module",
  "version": "1.0.0",
  "status": "active",
  "added_date": "2025-05-01",
  "files": [
    "references/modules/clause-8-4-supply-chain-guide.md",
    "assets/templates/modules/supply-chain-audit-checklist.md"
  ],
  "triggers": ["clause 8.4", "supplier", "external provider", "outsourced process"],
  "f1_priority_score": 0.0,
  "replaces": null,
  "notes": ""
}
```

## Activation gate

A module is activated when:
1. Its `status` is `active`.
2. Its files pass the controlled-source boundary check (no external URLs, all paths within `references/` or `assets/`).
3. It has been validated by `scripts/upskill_module_registry.py --validate <module_id>`.

A module with `status: pending` is not loaded. It exists in the registry for review purposes only.

## Hot-reload pattern

When the user uploads a new controlled-source document and asks the skill to learn from it:

1. Run `scripts/standard_ingestion_pipeline.py` to ingest the document.
2. Run `scripts/standard_index_builder.py` to rebuild the local RAG index.
3. Register the module with `scripts/upskill_module_registry.py --register`.
4. Set status to `pending` initially.
5. Run `scripts/upskill_module_registry.py --validate <module_id>` to check paths and boundary compliance.
6. Set status to `active` after validation passes.

The skill can use the new module immediately in the same session after step 6.

## Gating rules

- No module may load external references. If `files` contains a URL, the module fails validation.
- No module may override the governance files in `references/governance/`. Governance is immutable.
- No module may lower the CoV threshold, ethics rules, or evidence integrity rules. Modules can only extend scope, add templates, or add clause detail.
- A module that `replaces` an existing module must increment the version number and include a changelog note.

## F1-driven prioritization

The `f1_priority_score` field (range 0.0–1.0) is populated by `scripts/f1_tracker.py` after enough feedback is collected. A higher score means the corresponding area has lower F1 performance and is a higher priority for upskill.

The registry produces a prioritized upskill queue:

```bash
python scripts/upskill_module_registry.py --priority-queue
```

Output example:
```
Priority upskill queue (by F1 gap):
  1. clause_group: 8.4  f1: 0.71  → consider adding clause_guide_module for 8.4
  2. route: conformity_evaluation  f1: 0.74  → consider adding dialog_module for guided CE
  3. route: nc_classification (OBS verdicts)  f1: insufficient_data (n=3)  → collect more feedback
```

## Version management

Each module carries a `version` field in semver format (`MAJOR.MINOR.PATCH`).

- `PATCH` bump: editorial corrections, typo fixes.
- `MINOR` bump: new templates, added clause detail, extended trigger list.
- `MAJOR` bump: changed audit logic, replaced reference, breaking change.

The `replaces` field allows the skill to retire an old module when a new version is registered. The old module moves to `status: retired` and is no longer loaded.

## Immutable core

The following files are immutable and cannot be replaced or overridden by any module:

```
references/governance/closed-source-policy.md
references/governance/auditor-code-of-conduct.md
references/governance/evidence-integrity-rules.md
references/governance/refusal-and-escalation-rules.md
references/governance/controlled-output-rules.md
references/12-ethics-cov-escalation-rules.md
references/17-knowledge-boundary-enforcement.md
```

If a proposed module conflicts with any of these files, the module is rejected.

## v6.2 Audit World Model module classes
World-model coherence extensions may use existing `architecture_module`, `guardrail_module`, and `learning_governance_module` classes. A world-model module must not claim assurance authority. Before activation, validate state-equivalence logic, compression/distinction benchmarks, detour robustness, prediction/evidence separation, and deterministic-harness compatibility.
