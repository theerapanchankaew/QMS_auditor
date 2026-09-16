#!/usr/bin/env python3
"""AHP calculator for pairwise comparison matrices.

Usage:
    python scripts/ahp_calculator.py input.json

Input JSON:
{
  "criteria": ["C1", "C2", "C3"],
  "matrix": [[1,3,5],[0.3333333333,1,2],[0.2,0.5,1]]
}
"""
import json
import math
import sys

from controlled_source_guardrail import GuardrailDialogRequired, assert_no_external_payload, print_guardrail_and_exit

RI = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def criterion_id(item):
    if isinstance(item, dict):
        return str(item.get("id") or item.get("name") or item.get("criterion"))
    return str(item)


def _validate(criteria, matrix):
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("criteria must be a non-empty list")
    n = len(criteria)
    if not isinstance(matrix, list) or len(matrix) != n:
        raise ValueError("matrix must be square and match the number of criteria")
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != n:
            raise ValueError(f"row {i} must contain {n} values")
        for j, value in enumerate(row):
            if not isinstance(value, (int, float)) or value <= 0 or not math.isfinite(value):
                raise ValueError(f"matrix[{i}][{j}] must be a positive finite number")
    return n


def _matvec(matrix, vector):
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def _normalize(vector):
    total = sum(vector)
    if total <= 0:
        raise ValueError("cannot normalize a non-positive vector")
    return [x / total for x in vector]


def principal_eigenvector(matrix, max_iter=10000, tolerance=1e-12):
    n = len(matrix)
    vector = [1.0 / n] * n
    for _ in range(max_iter):
        next_vector = _normalize(_matvec(matrix, vector))
        diff = max(abs(next_vector[i] - vector[i]) for i in range(n))
        vector = next_vector
        if diff < tolerance:
            break
    weighted_sum = _matvec(matrix, vector)
    lambda_values = [weighted_sum[i] / vector[i] for i in range(n)]
    lambda_max = sum(lambda_values) / n
    return vector, lambda_max


def consistency_status(cr):
    if cr <= 0.10:
        return "acceptable"
    if cr <= 0.20:
        return "preliminary_only_review_recommended"
    return "review_required_inconsistent_judgments"


def calculate(criteria, matrix):
    n = _validate(criteria, matrix)
    ids = [criterion_id(c) for c in criteria]
    weights, lambda_max = principal_eigenvector(matrix)
    ci = 0.0 if n <= 2 else (lambda_max - n) / (n - 1)
    ri = RI.get(n)
    if ri is None:
        raise ValueError("RI is only defined for matrices up to size 10")
    cr = 0.0 if n <= 2 or ri == 0 else ci / ri
    return {
        "criteria": ids,
        "weights": {ids[i]: weights[i] for i in range(n)},
        "lambda_max": lambda_max,
        "ci": ci,
        "ri": ri,
        "cr": cr,
        "consistency_status": consistency_status(cr),
    }


def main(argv):
    if len(argv) != 2:
        print("Usage: python scripts/ahp_calculator.py input.json", file=sys.stderr)
        return 2
    data = _load(argv[1])
    try:
        assert_no_external_payload(data, context="AHP matrix input")
    except GuardrailDialogRequired as exc:
        return print_guardrail_and_exit(exc)
    result = calculate(data.get("criteria"), data.get("matrix"))
    result["source_guardrail"] = {"controlled_source_boundary": "enforced_in_code"}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
