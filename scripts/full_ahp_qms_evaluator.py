#!/usr/bin/env python3
"""Evaluate full AHP/QMS scoring inputs.

Usage:
    python scripts/full_ahp_qms_evaluator.py assets/templates/full-ahp-qms-input-template.json

The script calculates AHP criteria weights, consistency, weighted alternative scores, percent scores, and decision-support bands.
It is audit-support tooling only. It does not decide conformity or NC classification by itself.
"""
import json
import math
import sys
from pathlib import Path

from controlled_source_guardrail import GuardrailDialogRequired, assert_no_external_payload, print_guardrail_and_exit

RI = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def criterion_id(item):
    if isinstance(item, dict):
        return str(item.get("id") or item.get("name") or item.get("criterion"))
    return str(item)


def validate_matrix(criteria, matrix):
    n = len(criteria)
    if n == 0:
        raise ValueError("criteria must not be empty")
    if n > 10:
        raise ValueError("AHP RI table supports up to 10 criteria")
    if not isinstance(matrix, list) or len(matrix) != n:
        raise ValueError("matrix must be square and match criteria count")
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != n:
            raise ValueError(f"matrix row {i} must have {n} values")
        for j, value in enumerate(row):
            if not isinstance(value, (int, float)) or value <= 0 or not math.isfinite(value):
                raise ValueError(f"matrix[{i}][{j}] must be positive finite number")
    return n


def matvec(matrix, vector):
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def normalize(vector):
    total = sum(vector)
    if total <= 0:
        raise ValueError("cannot normalize vector")
    return [x / total for x in vector]


def eigen_weights(matrix, max_iter=10000, tolerance=1e-12):
    n = len(matrix)
    vector = [1.0 / n] * n
    for _ in range(max_iter):
        next_vector = normalize(matvec(matrix, vector))
        if max(abs(next_vector[i] - vector[i]) for i in range(n)) < tolerance:
            vector = next_vector
            break
        vector = next_vector
    weighted_sum = matvec(matrix, vector)
    lambda_max = sum(weighted_sum[i] / vector[i] for i in range(n)) / n
    return vector, lambda_max


def consistency_status(cr):
    if cr <= 0.10:
        return "acceptable"
    if cr <= 0.20:
        return "preliminary_only_review_recommended"
    return "review_required_inconsistent_judgments"


def support_band(percent):
    if percent >= 85:
        return "strongly_supported_conclusion"
    if percent >= 70:
        return "generally_supported_check_gaps"
    if percent >= 50:
        return "weak_or_partial_support_review_required"
    return "not_supported_or_likely_gap"


def calculate(data):
    criteria = data.get("criteria") or []
    ids = [criterion_id(c) for c in criteria]
    matrix = data.get("matrix")
    n = validate_matrix(ids, matrix)
    weights, lambda_max = eigen_weights(matrix)
    ci = 0.0 if n <= 2 else (lambda_max - n) / (n - 1)
    ri = RI[n]
    cr = 0.0 if n <= 2 or ri == 0 else ci / ri
    max_score = float(data.get("evaluation_scale", {}).get("max_score", 5))
    weight_map = {ids[i]: weights[i] for i in range(n)}

    alternatives = []
    for alt in data.get("alternatives", []):
        scores = alt.get("scores") or {}
        missing = [cid for cid in ids if cid not in scores]
        weighted_score = 0.0
        score_details = {}
        for cid in ids:
            raw = scores.get(cid, 0)
            if not isinstance(raw, (int, float)):
                raise ValueError(f"score for {alt.get('id', alt.get('name'))}/{cid} must be numeric")
            weighted = raw * weight_map[cid]
            weighted_score += weighted
            score_details[cid] = {"score": raw, "weight": weight_map[cid], "weighted": weighted}
        percent = 100.0 * weighted_score / max_score if max_score else 0.0
        alternatives.append({
            "id": alt.get("id"),
            "name": alt.get("name"),
            "weighted_score": weighted_score,
            "percent": percent,
            "decision_support": support_band(percent),
            "missing_scores": missing,
            "score_details": score_details,
            "audit_caution": "AHP supports priority and transparency only; verdict still requires clause-specific objective evidence."
        })

    return {
        "objective": data.get("objective"),
        "criteria": ids,
        "weights": weight_map,
        "lambda_max": lambda_max,
        "ci": ci,
        "ri": ri,
        "cr": cr,
        "consistency_status": consistency_status(cr),
        "alternatives": alternatives,
    }


def main(argv):
    if len(argv) != 2:
        print("Usage: python scripts/full_ahp_qms_evaluator.py input.json", file=sys.stderr)
        return 2
    data = load_json(argv[1])
    try:
        assert_no_external_payload(data, context="full AHP QMS input")
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)
    result = calculate(data)
    result["source_guardrail"] = {
        "controlled_source_boundary": "enforced_in_code",
        "external_source_policy": "blocked unless explicit per-run dialog confirmation is present",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
