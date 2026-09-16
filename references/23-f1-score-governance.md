# F1 Score Governance

## Purpose
Define how F1 score is computed, segmented, and used to adjust audit route behavior in the closed-loop QMS skill.

## F1 definition for audit verdicts

```
Precision  = TP / (TP + FP)
Recall     = TP / (TP + FN)
F1         = 2 × (Precision × Recall) / (Precision + Recall)
```

Where:
- **TP** (True Positive): AI said issue exists → user confirmed correct
- **FP** (False Positive): AI said issue exists → user said there was no issue
- **FN** (False Negative): AI said no issue or gave wrong verdict → user identified a real issue
- **TN**: AI said no issue → user confirmed correct (tracked but excluded from F1 in standard binary classification)

Partial feedback (0.5 TP + 0.5 FP) is included in the running calculation.

## Segmentation dimensions

F1 is tracked independently across three dimensions:

1. **By route**: `nc_classification`, `conformity_evaluation`, `predictive_risk_scoring`, `audit_workflow`, `iso_clause_advisor`, `full_ahp_evaluation`
2. **By clause group**: `4`, `5`, `6`, `7`, `8`, `8.4`, `8.5`, `9`, `10` (top-level or sub-clause)
3. **By verdict type**: `Major`, `Minor`, `OBS`, `OFI`, `Complied`, `InsufficientEvidence`

## Minimum sample thresholds

| Segment | Minimum feedback events before F1 is actionable |
|---|---|
| Route-level | 10 |
| Clause-group-level | 5 |
| Verdict-type-level | 5 |

Below the threshold, report F1 as `insufficient_data` and do not use it to adjust route behavior.

## F1 thresholds and behavior adjustment

| F1 range | Interpretation | Adjustment |
|---|---|---|
| ≥ 0.85 | High confidence | Proceed normally |
| 0.70 – 0.84 | Moderate | Increase CoV challenge threshold by one step |
| 0.50 – 0.69 | Low | Force `ReviewRequired` for all verdicts in this segment; flag to user |
| < 0.50 | Unreliable | Suspend that route/segment; always return `ReviewRequired` with explanation |

## F1 report output

```bash
python scripts/f1_tracker.py --report
```

Produces a JSON summary:

```json
{
  "generated_at": "<ISO 8601>",
  "overall_f1": 0.82,
  "by_route": {
    "nc_classification": { "f1": 0.88, "tp": 22, "fp": 3, "fn": 4, "n": 29 },
    "conformity_evaluation": { "f1": 0.74, "tp": 14, "fp": 5, "fn": 5, "n": 24 }
  },
  "by_clause_group": {
    "8.4": { "f1": 0.71, "n": 18, "flag": "moderate" },
    "9.1": { "f1": 0.90, "n": 12 }
  },
  "by_verdict_type": {
    "Major": { "f1": 0.85, "n": 20 },
    "Minor": { "f1": 0.79, "n": 30 },
    "OBS": { "f1": insufficient_data, "n": 3 }
  },
  "low_f1_alerts": [
    { "segment": "route:conformity_evaluation", "f1": 0.74, "action": "increase_cov" }
  ]
}
```

## F1-driven behavior adjustment rules

These rules modify the `references/08-verification-and-verdict-rules.md` strictness level at runtime:

1. **CoV intensity**: if F1 < 0.70 for a route, the chain-of-verification must challenge the draft verdict with at least two counter-hypotheses before finalizing.
2. **Evidence minimum**: if F1 < 0.70 for a clause group, require at least one additional evidence item beyond normal minimum.
3. **Escalation trigger**: if F1 < 0.50 for any segment, that segment always escalates to `ReviewRequired` with F1 flag shown to user.
4. **Suspension**: segments below 0.50 with ≥ 20 feedback events are flagged for upskill review before resuming full operation.

## Using F1 for upskill prioritization

The upskill module registry (`references/24-upskill-module-registry.md`) reads F1 stats to identify which clause groups or routes need a new or updated module. The registry's `priority_score` field is partially derived from `1 - F1` for that segment.

## Reset and calibration

F1 stats persist across sessions in `assets/stats/feedback_log.jsonl`. They can be reset per segment with:

```bash
python scripts/f1_tracker.py --reset-segment "route:nc_classification"
```

A reset requires a note justifying the reset (e.g. "major skill update invalidates prior data"). The reset is logged with a timestamp and note in a separate `assets/stats/f1_reset_log.jsonl`.

---

## v2.0 — 4-Dimensional F1 Tracking

Binary F1 alone is insufficient for measuring QMS audit intelligence. All four dimensions are required.

### Four F1 dimensions

| Dimension | Definition | Min threshold |
|---|---|---|
| **Binary F1** | Issue vs no-issue (Noncomplied/OFI/OBS vs Complied) | ≥0.90 |
| **Verdict F1** | Exact verdict match | ≥0.75 |
| **NC Class F1** | Major vs Minor accuracy | ≥0.70 |
| **Clause-specific F1** | Per clause group (4, 5, 6, 7, 8.3, 8.4, 8.5, 8.6, 8.7, 9, 10.2) | ≥0.70 per clause |

### Failure layer attribution

| F1 failure pattern | Failing layer | Fix |
|---|---|---|
| OFI vs Noncomplied | **L7** — conditional qualifier gate | Enforce L7 for 8.3, 8.5.3–8.5.5 |
| Major vs Minor mismatch | **L9–L11** — exposure/severity/counterfactual | Add Q1–Q5 + clause override |
| Wrong clause | **L5** — intent mapping | Load audit intent table |
| Complied vs InsufficientEvidence | **L4** — claim vs evidence | Enforce `implementation_proven` |

### Benchmark evaluation

For offline benchmark scoring (PRED vs GT):
- Use `scripts/benchmark_evaluator.py`
- Validate input files first with `scripts/testcase_schema_validator.py`
- Guardrail: `references/guardrails/evaluation-benchmark-guardrail.md`

**Benchmark F1 MUST NOT be written to `assets/stats/feedback_log.jsonl`** — it is read-only evaluation data.
