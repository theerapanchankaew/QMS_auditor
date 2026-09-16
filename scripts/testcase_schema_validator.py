#!/usr/bin/env python3
"""
testcase_schema_validator.py — QMS Auditor v1 Test Case Schema Validator
Purpose: Validate JSONL test case files and answer keys before benchmark evaluation.
         Catches field naming errors, missing required fields, invalid verdict values,
         and forbidden field usage before benchmark_evaluator.py runs.
Usage:
  python scripts/testcase_schema_validator.py --file <path.jsonl> --mode answer_key
  python scripts/testcase_schema_validator.py --file <path.jsonl> --mode prediction
  python scripts/testcase_schema_validator.py --file <path.jsonl> --mode testcase
"""
import argparse
import json
import os
import sys

# ── Field contracts ────────────────────────────────────────────────────────────
ANSWER_KEY_REQUIRED = {"case_id", "verdict", "nc_class"}
PREDICTION_REQUIRED = {"case_id", "generated_verdict", "generated_nc_class"}
TESTCASE_REQUIRED   = {"case_id", "clause", "evidence_summary"}

FORBIDDEN_IN_PREDICTION = {"expected_verdict", "expected_nc_class"}
FORBIDDEN_IN_ANSWER_KEY = {"generated_verdict", "generated_nc_class",
                            "expected_verdict", "expected_nc_class"}

VALID_VERDICTS = {
    "Complied", "Noncomplied", "OFI", "OBS",
    "InsufficientEvidence", "ReviewRequired",
    "OUT_OF_SCOPE", "ReferenceGap", "Unknown"
}
VALID_NC_CLASS = {"Major", "Minor", "None", "null", "", None}

NC_NORMALIZATION_MAP = {
    "": "None", "N/A": "None", "NA": "None",
    "n/a": "None", "na": "None", "none": "None",
    "null": "None", "Major": "Major", "major": "Major",
    "Minor": "Minor", "minor": "Minor"
}


def validate_file(path: str, mode: str) -> dict:
    if not os.path.exists(path):
        return {"status": "error", "error": f"File not found: {path}", "valid": False}

    if mode == "answer_key":
        required_fields = ANSWER_KEY_REQUIRED
        forbidden_fields = FORBIDDEN_IN_ANSWER_KEY
        verdict_field   = "verdict"
        nc_class_field  = "nc_class"
    elif mode == "prediction":
        required_fields = PREDICTION_REQUIRED
        forbidden_fields = FORBIDDEN_IN_PREDICTION
        verdict_field   = "generated_verdict"
        nc_class_field  = "generated_nc_class"
    elif mode == "testcase":
        required_fields = TESTCASE_REQUIRED
        forbidden_fields = set()
        verdict_field   = None
        nc_class_field  = None
    else:
        return {"status": "error", "error": f"Unknown mode: {mode}", "valid": False}

    errors    = []
    warnings  = []
    records   = []
    case_ids  = set()
    duplicate_ids = []

    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append({"line": line_num, "error": f"JSON decode error: {e}"})
                continue

            case_id = str(rec.get("case_id", f"<missing_line_{line_num}>"))
            if case_id in case_ids:
                duplicate_ids.append(case_id)
            case_ids.add(case_id)

            # ── Required fields check ──────────────────────────────────────
            for field in required_fields:
                if field not in rec:
                    errors.append({"line": line_num, "case_id": case_id,
                                   "error": f"Required field '{field}' missing"})

            # ── Forbidden fields check ─────────────────────────────────────
            for field in forbidden_fields:
                if field in rec:
                    errors.append({"line": line_num, "case_id": case_id,
                                   "error": f"Forbidden field '{field}' present in {mode}. "
                                            f"This field must NEVER be used as ground truth."})

            # ── Verdict validation ──────────────────────────────────────────
            if verdict_field and verdict_field in rec:
                v = rec[verdict_field]
                if v not in VALID_VERDICTS:
                    errors.append({"line": line_num, "case_id": case_id,
                                   "error": f"Invalid value for '{verdict_field}': '{v}'. "
                                            f"Valid: {sorted(VALID_VERDICTS)}"})

            # ── NC class normalization check ────────────────────────────────
            if nc_class_field and nc_class_field in rec:
                nc = rec[nc_class_field]
                normalized = NC_NORMALIZATION_MAP.get(str(nc) if nc is not None else "")
                if normalized is None:
                    warnings.append({"line": line_num, "case_id": case_id,
                                     "warning": f"Unrecognized nc_class value: '{nc}' — "
                                                f"will be treated as 'Unknown' in benchmark."})
                elif nc in ("", "N/A", "NA", "n/a", "null", "none") and normalized == "None":
                    warnings.append({"line": line_num, "case_id": case_id,
                                     "warning": f"nc_class '{nc}' normalized to 'None'. "
                                                f"Use null/None in JSON for cleaner data."})

            records.append(rec)

    result = {
        "status": "valid" if not errors else "invalid",
        "valid": len(errors) == 0,
        "mode": mode,
        "file": os.path.basename(path),
        "total_records": len(records),
        "unique_case_ids": len(case_ids),
        "duplicate_case_ids": duplicate_ids,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors[:50],      # cap at 50 for readability
        "warnings": warnings[:20],
    }

    if mode == "answer_key":
        result["field_contract"] = {
            "GT_verdict_field": "verdict",
            "GT_nc_class_field": "nc_class",
            "forbidden_fields": sorted(FORBIDDEN_IN_ANSWER_KEY)
        }
    elif mode == "prediction":
        result["field_contract"] = {
            "PRED_verdict_field": "generated_verdict",
            "PRED_nc_class_field": "generated_nc_class",
            "forbidden_fields": sorted(FORBIDDEN_IN_PREDICTION)
        }

    return result


def main():
    parser = argparse.ArgumentParser(description="QMS Test Case Schema Validator")
    parser.add_argument("--file",  type=str, required=True,
                        help="Path to JSONL file to validate")
    parser.add_argument("--mode",  type=str, required=True,
                        choices=["answer_key", "prediction", "testcase"],
                        help="Validation mode: answer_key | prediction | testcase")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any errors found")
    args = parser.parse_args()

    result = validate_file(args.file, args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.strict and not result["valid"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
