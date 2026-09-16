# Evaluation & Benchmark Mode Guardrail — v1.0
> **Scope:** Applies whenever the task involves comparing AI-generated audit output against an answer key, computing accuracy/F1, or generating a Consolidated Audit Evaluation Report.
> **Priority:** P0 — enforced before any scoring, verdict comparison, or report generation step.

---

## 1. Mode Detection

Activate **BENCHMARK_MODE** when the user request contains any of:
- "evaluate", "benchmark", "score", "accuracy", "F1", "consolidated report", "answer key", "ground truth", "prediction vs expected", "compare output", "ประเมินผล", "เปรียบเทียบผล"
- Two input files where one is a `.jsonl` answer key AND another is a generated report (`.md`, `.json`, `.csv`)

Once BENCHMARK_MODE is active, **all rules in this file take mandatory priority** over normal audit reasoning workflow.

---

## 2. Canonical Source Roles — NEVER SWAP

| Role | Canonical Source | Fields to extract |
|---|---|---|
| **Ground Truth (GT)** | `qms_9001_answer_key.jsonl` only | `case_id`, `verdict`, `nc_class` |
| **Prediction (PRED)** | Generated audit report only (e.g. `qms_AUDIT_REPORT_*.md`) | `generated_verdict`, `generated_nc_class` |

### ❌ Forbidden source swaps (will invalidate the entire evaluation):

| Forbidden action | Why it fails |
|---|---|
| Reading `expected_verdict` from the markdown report as GT | The report's `expected_*` columns are display-only copies — NOT authoritative GT |
| Reading `nc_class` from the report's `expected_nc_class` column as GT | Same reason — display copy, not source-of-truth |
| Looking for `expected_nc_class` field in the JSONL | JSONL GT field name is `nc_class`, not `expected_nc_class` |
| Re-evaluating audit logic from evidence to produce a new verdict | BENCHMARK_MODE scores the existing prediction — do NOT re-derive verdicts |
| Using any field from the generated report as GT | The report is PRED only |

### ✅ Correct field mapping contract:

```
JSONL record:
  case_id         → join key
  verdict         → GT_verdict       (canonical ground truth)
  nc_class        → GT_nc_class      (canonical ground truth; may be null/None/"")

Generated report row (per case_id):
  generated_verdict   → PRED_verdict
  generated_nc_class  → PRED_nc_class  (may be blank / None / N/A)
```

**Before any computation, verify this mapping explicitly:**
```
ASSERT: GT_verdict source = JSONL field "verdict"
ASSERT: PRED_verdict source = report field "generated_verdict"
ASSERT: GT_nc_class source = JSONL field "nc_class"
ASSERT: PRED_nc_class source = report field "generated_nc_class"
```
If any ASSERT cannot be confirmed → stop and report `BENCHMARK_SOURCE_ERROR` to the user.

---

## 3. NC Class Normalization — Blank / None / N/A

Before any comparison or F1 computation, normalize NC class values using this table:

| Raw value | Normalized form | Condition |
|---|---|---|
| `""` (empty string) | `None` | Always |
| `null`, `None`, `NaN` | `None` | Always |
| `"N/A"`, `"n/a"`, `"NA"` | `None` | Always |
| `"Major"`, `"major"`, `"MAJOR"` | `Major` | Case-insensitive |
| `"Minor"`, `"minor"`, `"MINOR"` | `Minor` | Case-insensitive |
| Any other value | `Unknown` | Flag as anomaly |

**Critical rules:**
- A GT_nc_class of `None` means the case is classified as Complied/OFI — NC class comparison does not apply for this case.
- A PRED_nc_class of `None` when GT_nc_class is `Major` or `Minor` is a **miss** (not a match).
- NC class comparison is only performed when GT_nc_class is `Major` or `Minor`.
- `Strict NC Classification Accuracy` = correct PRED_nc_class / total cases where GT_nc_class ∈ {Major, Minor}.
- `Overall NC Classification Accuracy` = correct PRED_nc_class / total cases (treating None→None as correct for Complied cases).

---

## 4. Verdict Comparison Rules

Normalize verdicts before comparison:

| Raw value | Normalized |
|---|---|
| `"Complied"`, `"complied"`, `"COMPLIED"` | `Complied` |
| `"Noncomplied"`, `"noncomplied"`, `"NonComplied"` | `Noncomplied` |
| `"OFI"`, `"ofi"` | `OFI` |
| `"OBS"`, `"obs"` | `OBS` |
| `"InsufficientEvidence"` | `InsufficientEvidence` |
| `"ReviewRequired"` | `ReviewRequired` |
| `""`, `null`, `None` | `Unknown` — count as mismatch |

**Binary verdict accuracy** collapses to: `Complied` vs `Noncomplied` (all other verdicts map to `Noncomplied` for binary scoring unless explicitly scoped otherwise).

---

## 5. F1 Computation for Benchmark Mode

Use only PRED vs GT after normalization. Never use report-internal `expected_*` columns for F1.

```
Binary classification:
  Positive class = Noncomplied
  Negative class = Complied

TP = GT=Noncomplied AND PRED=Noncomplied
FP = GT=Complied AND PRED=Noncomplied
FN = GT=Noncomplied AND PRED=Complied
TN = GT=Complied AND PRED=Complied

Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 × Precision × Recall / (Precision + Recall)
```

If denominator is zero, report F1 as `undefined` (not 0.0).

---

## 6. Failed-Case Grouping

A case is a **failed case** when PRED_verdict ≠ GT_verdict (after normalization).

Group failed cases by:
1. **False Positive** — PRED=Noncomplied, GT=Complied
2. **False Negative** — PRED=Complied, GT=Noncomplied
3. **NC Class Mismatch** — Verdict matched but PRED_nc_class ≠ GT_nc_class (within Noncomplied cases)
4. **Verdict Mismatch (Other)** — Neither above binary class (e.g. OFI vs Complied)

Each failed case entry MUST include: `case_id`, `GT_verdict`, `PRED_verdict`, `GT_nc_class`, `PRED_nc_class`, `failure_type`.

---

## 7. Pre-Computation Checklist

Before generating any consolidated report or score, execute this checklist:

```
[ ] 1. Source roles confirmed: JSONL = GT, Report = PRED
[ ] 2. Field mapping verified: GT uses "verdict"+"nc_class"; PRED uses "generated_verdict"+"generated_nc_class"
[ ] 3. No expected_* columns from report used as GT
[ ] 4. NC class values normalized (blank/None/N/A → None)
[ ] 5. Verdict values normalized (case-insensitive)
[ ] 6. case_id join verified — no unmatched cases dropped silently
[ ] 7. Total case count confirmed before and after join
[ ] 8. Re-derivation of verdicts from evidence NOT performed (PRED taken as-is from report)
```

If any item is unchecked → halt and report which item failed to the user.

---

## 8. Consolidated Report Required Sections

A valid Consolidated Audit Evaluation Report MUST include all of the following in order:

```markdown
## 1. Source Verification
- GT source: [file name] — field mapping confirmed
- PRED source: [file name] — field mapping confirmed
- Total cases in GT: N
- Total cases in PRED: N
- Cases after join: N (note any dropped)

## 2. Case Distribution
- GT Complied: N
- GT Noncomplied: N
  - GT Major NC: N
  - GT Minor NC: N
- PRED Complied: N
- PRED Noncomplied: N

## 3. Accuracy Metrics
- Verdict Accuracy: X.X%
- Strict NC Classification Accuracy: X.X%
- Overall NC Classification Accuracy: X.X%
- F1 Score: X.XXX (Precision: X.XXX, Recall: X.XXX)

## 4. Confusion Matrix
| | PRED Complied | PRED Noncomplied |
|---|---|---|
| GT Complied | TN | FP |
| GT Noncomplied | FN | TP |

## 5. Failed Cases (N total)
[table: case_id | GT_verdict | PRED_verdict | GT_nc_class | PRED_nc_class | failure_type]

## 6. Source Integrity Declaration
- GT fields used: verdict, nc_class (from JSONL)
- PRED fields used: generated_verdict, generated_nc_class (from report)
- No expected_* columns from report used as GT: CONFIRMED
- No re-derivation of verdicts performed: CONFIRMED
```

---

## 9. Error Codes

| Code | Meaning | Action |
|---|---|---|
| `BENCHMARK_SOURCE_ERROR` | Source role swap detected | Stop — report to user, do not compute |
| `BENCHMARK_FIELD_ERROR` | Wrong field name used (e.g. expected_nc_class from JSONL) | Stop — report to user |
| `BENCHMARK_REEVAL_DETECTED` | System attempted to re-derive verdict from evidence | Stop — use existing PRED |
| `BENCHMARK_JOIN_ERROR` | case_id mismatch between GT and PRED | Report dropped cases, continue with matched set only |
| `BENCHMARK_NORMALIZATION_WARNING` | Unknown value encountered during normalization | Flag as anomaly, count as mismatch |


## Hardened Real Model Performance Addendum

For real model performance, use `references/34-evaluation-harness-protocol.md` and require `model_predictions.jsonl` generated from sanitized inputs. Do not compare answer-key files to claim model performance. Remove label-leaking fields before inference, including `expected_verdict`, `expected_nc_class`, `finding_expected_verdict`, `finding_expected_nc_class`, `answer_rationale`, `finding_basis`, `trigger_or_anchor`, `gold_verdict`, `gold_nc_class`, `verdict`, and `nc_class` when those fields act as gold labels.

Canonical commands:

```bash
python scripts/prepare_model_performance_inputs.py --source <testcases_or_answer_key.jsonl> --outdir qms_model_performance_inputs
python scripts/evaluate_model_predictions.py --gold <gold_answer_key.jsonl> --pred model_predictions.jsonl --outdir qms_model_performance_results
```
