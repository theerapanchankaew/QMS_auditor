# QMS Context Window Management

Use this reference for long, multi-file, benchmark, or source-heavy QMS tasks. The purpose is to keep the context window lean, repeatable, and traceable.

## Progressive loading rule

Load only the context pack required by the selected route. Do not load all references by default.

| Task mode | Required context pack |
|---|---|
| `definition_lookup` | `SKILL.md`, closed-source governance, `references/standard/iso9001-2026-definition-index.md`, `references/standard/iso9000-2026-vocabulary-source-map.md`, `scripts/local_source_resolver.py`. |
| `clause_advisor` | Governance, `references/03-route-decision-map.md`, `references/27-clause-requirement-profiles.md`, relevant standard map/guide. |
| `conformity_evaluation` | Governance, `references/26-layered-audit-cognition.md`, `references/27-clause-requirement-profiles.md`, `references/28-evidence-schema.md`, relevant evidence. |
| `nc_classification` | Conformity pack plus `references/10-nc-classification-rules.md`, `references/25-nc-severity-calibration-guide.md`. |
| `audit_workflow` | Governance, route map, output templates, supplied audit scope/evidence. |
| `benchmark_mode` | `references/guardrails/evaluation-benchmark-guardrail.md`, `references/34-evaluation-harness-protocol.md`, prediction schema, evaluator scripts. |
| `harness_report` | `references/29-harnesscard-qms-auditor.md`, `30-control-layer-contract.md`, `31-agency-action-surface.md`, `32-context-window-management.md`, `33-runtime-recovery-and-repeatability.md`. |

## Context ledger

For tasks involving more than one uploaded file, more than one evaluation pass, or more than three source references, maintain a context ledger using `assets/templates/context-ledger-template.json`.

Required ledger fields:
- `task_mode`
- `route`
- `loaded_sources`
- `excluded_sources`
- `evidence_inventory`
- `open_questions`
- `decision_state`

## Controlled compaction

When context is large, preserve:
- user objective;
- evidence inventory;
- clause candidates;
- decision gates already passed;
- unresolved evidence gaps;
- source trace and file names;
- benchmark source roles.

Drop or compress:
- repeated boilerplate;
- rejected draft wording;
- irrelevant branches;
- duplicated snippets;
- non-controlling commentary.

Never compact away the source boundary, gold/prediction role separation, or decisive evidence gaps.

---

## Advisory-only notice on compaction enforcement (v1.1)

The controlled compaction rules above are **advisory guidance for the language model**, not programmatically enforced constraints. There is no script in `scripts/**` that can verify which tokens the model actually retains or drops within its context window.

**What this means in practice:**
- The context ledger (`assets/templates/context-ledger-template.json`) provides a structured record of what *should* be in scope, but its contents are written by the model, not independently audited.
- `validate_context_ledger.py` checks the ledger *schema* (required fields, excluded_sources contains "web"), not the *accuracy* of what the model reports.
- Compaction fidelity is therefore a **model compliance concern**, not a deterministic harness guarantee.

**Mitigation:** For high-stakes long tasks, the auditor should:
1. Keep tasks short enough that compaction is unnecessary when possible.
2. Re-state the user objective and critical source roles explicitly at the start of each evaluation pass.
3. Use `decision_state` in the context ledger to checkpoint the most recent verdict/gate result, so it can be re-supplied if context is trimmed.
4. Treat any output that omits a required source trace as a potential compaction failure and re-run with a fresh context.

**Future improvement path:** A multi-turn harness wrapper that injects the context ledger into every turn could reduce compaction risk systematically. That architecture is outside the scope of this single-session skill.
