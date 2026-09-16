#!/usr/bin/env python3
"""
dialog_confirmation_gate.py — QMS Auditor v1.1 Dialog Confirmation Gate (Gate 3)
Purpose: Enforce L7/L9/L10/L11 constraints before finalizing any verdict.
v1.1: Added cognition engine enforcement (L7 OFI block, M-trigger, D-anchor, confidence).
Usage:
  python scripts/dialog_confirmation_gate.py
    --action "<action>"
    --clause "<clause>"
    --evidence-summary "<summary>"
    --verdict-draft "<verdict>"
    [--nc-class "Major|Minor"]
    [--trigger "M1|M2|M3|M4|M5|D1|D2|D3|D4"]
    [--decisive-question "<question>"]
    [--confidence 0.85]
    [--l7-result "OFI|applies|not_applicable"]
    [--conditional-qualifier-checked "yes|no|not_applicable"]
"""
import argparse
import json
import sys
import re

VALID_VERDICTS = {
    "complied","noncomplied","noncomplied/major","noncomplied/minor",
    "nc/major","nc/minor","ofi","obs","insufficientevidence",
    "reviewrequired","out_of_scope","referencegap","informational"
}
MAJOR_VERDICTS   = {"noncomplied/major","nc/major"}
NC_VERDICTS      = {"noncomplied","noncomplied/major","noncomplied/minor","nc/major","nc/minor"}
VALID_M_TRIGGERS = {"m1","m2","m3","m4","m5"}
VALID_D_ANCHORS  = {"d1","d2","d3","d4"}
VALID_TRIGGERS   = VALID_M_TRIGGERS | VALID_D_ANCHORS
CLAUSE_PATTERN   = re.compile(r"^\d+(\.\d+)*(\s+\w.*)?$")
CONDITIONAL_KW   = [
    "as applicable","as appropriate","to the extent necessary",
    "where applicable","if applicable","if practicable","where practicable",
    "when relevant","when it is necessary","as required by"
]
# Implementation-heavy clauses: policy alone ≠ Complied
IMPL_HEAVY = {"8.3","8.4","8.5","8.6","8.7","9.2","10.2"}


def check_clause(clause):
    c = clause.strip()
    if not c:
        return {"valid": False, "issue": "clause_missing"}
    if not CLAUSE_PATTERN.match(c):
        return {"valid": False, "issue": f"unrecognized_clause_format: '{c}'"}
    return {"valid": True, "clause": c}


def detect_conditional(evidence, clause):
    text = (evidence + " " + clause).lower()
    return any(kw in text for kw in CONDITIONAL_KW)


def main():
    parser = argparse.ArgumentParser(description="QMS Dialog Confirmation Gate v1.1")
    parser.add_argument("--action",                       type=str, default="")
    parser.add_argument("--clause",                       type=str, default="")
    parser.add_argument("--evidence-summary",             type=str, default="")
    parser.add_argument("--verdict-draft",                type=str, default="")
    parser.add_argument("--nc-class",                     type=str, default="",
                         choices=["Major","Minor","major","minor",""])
    parser.add_argument("--trigger",                      type=str, default="")
    parser.add_argument("--decisive-question",            type=str, default="")
    parser.add_argument("--confidence",                   type=float, default=0.0)
    parser.add_argument("--l7-result",                    type=str, default="",
                         choices=["OFI","applies","not_applicable",""])
    parser.add_argument("--conditional-qualifier-checked",type=str, default="not_applicable",
                         choices=["yes","no","not_applicable"])
    args = parser.parse_args()

    errors   = []
    warnings = []
    v_lower  = args.verdict_draft.strip().lower()

    # ── Basic validation ────────────────────────────────────────────────────
    clause_check = check_clause(args.clause)
    if not clause_check["valid"]:
        warnings.append(clause_check["issue"])

    if v_lower and v_lower not in VALID_VERDICTS:
        errors.append({"issue": f"invalid_verdict: '{args.verdict_draft}'",
                        "valid_options": sorted(VALID_VERDICTS)})

    if not args.action.strip():
        warnings.append("action_field_empty")

    # ── L7: Conditional qualifier enforcement ─────────────────────────────
    has_cond = detect_conditional(args.evidence_summary, args.clause)
    if has_cond and args.conditional_qualifier_checked == "no":
        warnings.append({"issue": "conditional_qualifier_detected_L7_not_run",
                          "detail": "Run L7 conditional qualifier gate before finalizing."})
    if v_lower in NC_VERDICTS and has_cond and args.l7_result == "OFI":
        errors.append({"issue": "L7_says_OFI_but_verdict_is_NC",
                        "detail": "L7 returned OFI (condition not assessed). Downgrade to OFI."})

    # ── L8: Evidence adequacy for NC ──────────────────────────────────────
    if v_lower in NC_VERDICTS and len(args.evidence_summary.strip()) < 20:
        errors.append({"issue": "nc_insufficient_evidence_summary",
                        "detail": "NC verdict requires evidence summary ≥20 chars with breach proof."})

    # ── L10: Implementation-heavy clause — Complied check ─────────────────
    clause_base = args.clause.strip().split()[0] if args.clause else ""
    if v_lower == "complied" and clause_base in IMPL_HEAVY:
        ev_lower = args.evidence_summary.lower()
        if any(kw in ev_lower for kw in ["procedure only","policy only","only procedure","only policy","verbal claim","no records"]):
            errors.append({"issue": "complied_from_procedure_only_on_implementation_heavy_clause",
                            "detail": f"Clause {clause_base} is implementation-heavy. "
                                      f"Policy/procedure alone cannot support Complied. "
                                      f"Verify implementation_proven = true and record_proven = true."})

    # ── L9/L10: Major — M-trigger required ───────────────────────────────
    if v_lower in MAJOR_VERDICTS or (v_lower == "noncomplied" and args.nc_class.lower() == "major"):
        trigger = args.trigger.strip().lower()
        if not trigger:
            errors.append({"issue": "major_nc_missing_m_trigger",
                            "detail": "Major NC requires --trigger M1|M2|M3|M4|M5."})
        elif trigger not in VALID_M_TRIGGERS:
            errors.append({"issue": f"major_nc_invalid_trigger: '{args.trigger}'",
                            "detail": "Major trigger must be M1, M2, M3, M4, or M5."})
        if not args.decisive_question.strip():
            errors.append({"issue": "major_nc_missing_decisive_question",
                            "detail": "Major NC requires --decisive-question."})

    # ── L10: Minor — D-anchor recommended ────────────────────────────────
    is_minor = (v_lower in {"noncomplied/minor","nc/minor"} or
                (v_lower == "noncomplied" and args.nc_class.lower() == "minor"))
    if is_minor:
        trigger = args.trigger.strip().lower()
        if not trigger:
            warnings.append({"issue": "minor_nc_missing_d_anchor",
                              "detail": "Minor NC should include --trigger D1|D2|D3|D4."})
        elif trigger not in VALID_D_ANCHORS:
            warnings.append({"issue": f"minor_nc_unexpected_trigger: '{args.trigger}'",
                              "detail": "Minor anchor should be D1, D2, D3, or D4."})

    # ── L11/L12: Confidence gate ──────────────────────────────────────────
    if args.confidence > 0:
        if v_lower in MAJOR_VERDICTS and args.confidence < 0.70:
            errors.append({"issue": "major_nc_confidence_too_low",
                            "detail": f"Confidence {args.confidence} < 0.70 for Major NC. Escalate to ReviewRequired."})
        elif v_lower in NC_VERDICTS and args.confidence < 0.60:
            errors.append({"issue": "nc_confidence_below_0.60",
                            "detail": f"Confidence {args.confidence} < 0.60. Use InsufficientEvidence."})
        elif v_lower in NC_VERDICTS and args.confidence < 0.80:
            warnings.append({"issue": "nc_confidence_below_0.80",
                              "detail": f"Confidence {args.confidence} → ReviewRequired recommended."})

    # ── Result ──────────────────────────────────────────────────────────
    if errors:
        result = {
            "gate_result": "blocked",
            "errors": errors,
            "warnings": warnings,
            "action": "resolve_errors_before_output",
            "cognition_layers_to_recheck": list({
                e["issue"].split("_")[0].upper()
                for e in errors if isinstance(e, dict) and "issue" in e
            })
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(2)

    result = {
        "gate_result": "confirmed",
        "clause":           args.clause or "not_specified",
        "verdict":          args.verdict_draft,
        "nc_class":         args.nc_class or "null",
        "trigger":          args.trigger or "null",
        "decisive_question": args.decisive_question or "null",
        "confidence":       args.confidence if args.confidence > 0 else "not_specified",
        "l7_result":        args.l7_result or "not_specified",
        "warnings":         warnings,
        "action":           "proceed_to_output"
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
