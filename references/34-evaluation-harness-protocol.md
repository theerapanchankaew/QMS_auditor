# QMS Evaluation Harness Protocol

Use this workflow when the user asks to measure real model performance, generate `model_predictions.jsonl`, compute F1, create a benchmark package, or analyze errors.

## Objective

Measure actual model+harness performance by separating inference from scoring:

1. Sanitized testcase input goes to the model.
2. Model output is saved as `model_predictions.jsonl`.
3. Gold answer key remains hidden until scoring.
4. Evaluation joins gold and prediction by `case_id`.

Do not compute performance by comparing two gold/expected-label files. That is label consistency, not real model performance.

## Required model prediction schema

File name: `model_predictions.jsonl`

Each line must be one JSON object:

```json
{"case_id":"QMS9001-CASE-00001","predicted_verdict":"Noncomplied","predicted_nc_class":"Minor","predicted_clause":"8.7","predicted_trigger_or_anchor":"D2","rationale":"Brief QMS audit reasoning."}
```

Required fields:
- `case_id`
- `predicted_verdict`
- `predicted_nc_class`

Allowed verdict values:
- `Complied`
- `Noncomplied`
- `OFI`
- `OBS`
- `InsufficientEvidence`
- `ReviewRequired`
- `ReferenceGap`
- `OUT_OF_SCOPE`

Allowed NC class values:
- `Major`
- `Minor`
- `None`
- `null` or empty string, normalized to `None`

Optional fields:
- `predicted_clause`
- `predicted_trigger_or_anchor`
- `predicted_evidence_gap`
- `rationale`

## Scoring command

```bash
python scripts/evaluate_model_predictions.py --gold <gold_answer_key.jsonl> --pred model_predictions.jsonl --outdir <results_dir>
```

## Primary metrics

1. Composite Verdict+NC Class Macro F1.
2. Verdict Macro F1.
3. NC Class Macro F1.
4. Major Recall.
5. Clause F1.
6. Trigger/Anchor F1.
7. Error analysis by clause, process, sector, and trigger.

## Required report statement

Every performance report must state whether it is:
- real model performance: hidden gold vs `model_predictions.jsonl` created from sanitized inputs; or
- label consistency only: expected labels compared with another answer-key file.
