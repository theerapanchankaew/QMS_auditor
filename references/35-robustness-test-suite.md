# QMS Robustness Test Suite

Use this reference after skill edits, before packaging, or when the user asks for robustness/repeatability checks.

## Regression groups

| Group | File | Purpose |
|---|---|---|
| Source boundary | `assets/tests/source-boundary-regression.jsonl` | Ensure web/external requests are blocked or converted to controlled-source requests. |
| Scope gate | `assets/tests/scope-gate-regression.jsonl` | Ensure non-QMS standalone requests return `OUT_OF_SCOPE`. |
| Label leakage | `assets/tests/label-leakage-regression.jsonl` | Ensure benchmark mode removes expected/gold fields before inference. |
| NC classification | `assets/tests/qms-nc-classification-regression.jsonl` | Ensure M1-M5/D1-D4 logic and ReviewRequired behavior are stable. |
| Context window | `assets/tests/context-window-regression.jsonl` | Ensure context ledger and compaction preserve source trace. |

## Regression command

```bash
python scripts/run_regression_suite.py --skill-root . --outdir regression_results
```

## Pass condition

A hardened package should pass all structural checks. Content-level audit verdict checks are smoke tests and must remain conservative; they do not replace human technical review.
