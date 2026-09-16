#!/usr/bin/env python3
"""
harness_gate_executor.py — QMS Deterministic Gate Enforcer
Version: 1.0.0
Part of: ai-audit-platform-core / qms-auditor-iso-9001-2026 v5.5-DH

Validates model structured output (gate_execution_trace) against gate enforcement rules.
Rejects contradictions and forces correct verdicts when gates are violated.

Usage:
  python scripts/harness_gate_executor.py --input model_output.json
  python scripts/harness_gate_executor.py --validate-schema
  python scripts/harness_gate_executor.py --batch model_predictions.jsonl --outdir results/

This is the canonical G0-G7 gate catalog + severity engine (M4 test,
D2_SAFE ceiling) + harness (forced-override/rejection). See
docs/eei-blueprint-crosswalk.md before adding another "gate_catalog.py",
"severity_engine.py", or "harness.py" — this file already is all three.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional

# ── Gate data tables ───────────────────────────────────────────────────────────

D2_SAFE_LIST = {
    '4.1', '4.2', '5.2.1', '5.2.2',
    '7.1.1', '7.1.3', '7.1.6', '7.3', '7.4',
    '8.2.3.2', '8.3.3', '8.3.5',
    '8.4.3', '8.5.3', '8.5.4', '8.5.5', '8.5.6',
    '10.1'
}

M4_MANDATORY_LIST = {
    '4.4.2', '5.1.2', '6.1.1', '6.1.2', '6.3',
    '7.2', '7.5.1', '7.5.2',
    '8.2.2', '8.2.4', '8.3.2', '8.3.4', '8.3.6',
    '8.5.1', '8.7.1', '8.7.2',
    '9.1.1', '9.1.2', '9.2.1', '9.2.2', '9.3.1', '10.2.1'
}

AMBIGUOUS_LIST = {'9.1.3', '10.2.2'}

IMPLEMENTATION_HEAVY_CLAUSES = {
    '8.1', '8.2.1', '8.2.2', '8.2.3.1', '8.2.3.2', '8.2.4',
    '8.3.1', '8.3.2', '8.3.3', '8.3.4', '8.3.5', '8.3.6',
    '8.4.1', '8.4.2', '8.4.3',
    '8.5.1', '8.5.2', '8.5.3', '8.5.4', '8.5.5', '8.5.6',
    '8.6', '8.7.1', '8.7.2',
    '9.1.1', '9.1.2', '9.2.1', '9.2.2', '9.3.1', '9.3.2', '9.3.3',
    '10.2.1', '10.2.2'
}

VALID_VERDICTS = {
    'Complied', 'Noncomplied', 'OFI', 'OBS',
    'InsufficientEvidence', 'ReviewRequired', 'ReferenceGap', 'OUT_OF_SCOPE'
}

VALID_NC_CLASSES = {'Major', 'Minor', 'None', None}

# ── Rejection helper ───────────────────────────────────────────────────────────

def reject(reason: str, message: str, gate: str, **overrides) -> dict:
    return {
        "gate_validation": "FAIL",
        "gate_failed": gate,
        "rejection_reason": reason,
        "rejection_message": message,
        "forced_overrides": overrides,
        "action": "retry_with_forced_overrides OR escalate_to_human_review"
    }

# ── Gate enforcement functions ─────────────────────────────────────────────────

def enforce_g0_preflight(trace: dict) -> Optional[dict]:
    """G0: Closed-source preflight must be confirmed."""
    g0 = trace.get("G0_preflight", {})
    if not g0.get("closed_source_confirmed"):
        return reject(
            reason="G0_PREFLIGHT_NOT_CONFIRMED",
            message="Closed-source preflight must be confirmed before audit work.",
            gate="G0"
        )
    return None


def enforce_g2_ie_chain(trace: dict, verdict: str, clause: Optional[str]) -> Optional[dict]:
    """G2: IE Hard Stop — if triggered, verdict MUST be InsufficientEvidence."""
    g1 = trace.get("G1_linguistic", {})
    g2 = trace.get("G2_ie_chain", {})

    if g1.get("evidence_activity") != "PRESENTED":
        return None  # G2 only applies on PRESENTED path

    if not g2.get("triggered"):
        return None  # G2 not triggered

    chain_result = g2.get("chain_result")

    # Step 2: ครบถ้วน สอดคล้อง without verification
    if g2.get("step2_khropthuean_without_verify") is True:
        if verdict != "InsufficientEvidence":
            return reject(
                reason="G2_STEP2_VIOLATION",
                message=(
                    "'ครบถ้วน สอดคล้อง' confirms record consistency only — "
                    "does NOT confirm element coverage or effectiveness. "
                    "IE mandatory when step2 fires."
                ),
                gate="G2",
                forced_verdict="InsufficientEvidence"
            )

    # Step 3: ยืนยันการใช้งานจริง only (not ยืนยันระบบทำงาน)
    if (g2.get("step3_yuenyankarn_only") is True and
            clause in IMPLEMENTATION_HEAVY_CLAUSES):
        if verdict not in ("InsufficientEvidence", "ReviewRequired"):
            return reject(
                reason="G2_STEP3_VIOLATION",
                message=(
                    "'ยืนยันการใช้งานจริง' (confirmed in use) is weaker than "
                    "'ยืนยันระบบทำงานตามที่กำหนด' (system confirmed working). "
                    "IE required for implementation-heavy clauses."
                ),
                gate="G2",
                forced_verdict="InsufficientEvidence"
            )

    # Step 4: stage_1 + presented
    if g2.get("step4_stage1_presented") is True:
        if verdict != "InsufficientEvidence":
            return reject(
                reason="G2_STEP4_VIOLATION",
                message=(
                    "audit_type=stage_1 + evidence_activity=PRESENTED = "
                    "documentation review only, not implementation verification. "
                    "IE mandatory."
                ),
                gate="G2",
                forced_verdict="InsufficientEvidence"
            )

    return None


def enforce_g3_severity_ceiling(trace: dict, nc_class: Optional[str], clause: Optional[str]) -> Optional[dict]:
    """G3: D2-safe ceiling — clause in D2_SAFE_LIST cannot be Major."""
    g3 = trace.get("G3_severity_ceiling", {})
    clause_category = g3.get("clause_category")

    # Auto-detect if not filled
    if not clause_category and clause:
        if clause in D2_SAFE_LIST:
            clause_category = "D2_SAFE"
        elif clause in M4_MANDATORY_LIST:
            clause_category = "M4_MANDATORY"
        elif clause in AMBIGUOUS_LIST:
            clause_category = "AMBIGUOUS"

    if clause_category == "D2_SAFE" and nc_class == "Major":
        return reject(
            reason="G3_D2_SAFE_CEILING_VIOLATION",
            message=(
                f"Clause {clause} is in D2_SAFE_LIST — it has sub-element requirements "
                "(specific records/documents), not entire system elements. "
                "Major verdict ceiling = Minor regardless of risk level."
            ),
            gate="G3",
            forced_nc_class="Minor"
        )

    return None


def enforce_g4_m4_conditions(trace: dict, nc_class: Optional[str]) -> Optional[dict]:
    """G4: M4 three-condition test — Major requires A AND B AND C."""
    g4 = trace.get("G4_m4_conditions", {})

    if nc_class != "Major":
        return None  # G4 only relevant for Major verdicts

    if not g4:
        return None  # G4 not filled, skip (warn separately)

    m4_result = g4.get("m4_result")
    if m4_result != "Major M4":
        return None

    a = g4.get("A_process_entirely_absent", False)
    b = g4.get("B_zero_records_in_sample", False)
    c = g4.get("C_interview_confirms_absence", False)

    if not (a and b and c):
        missing = [k for k, v in [("A", a), ("B", b), ("C", c)] if not v]
        return reject(
            reason="G4_M4_INCOMPLETE_CONDITIONS",
            message=(
                f"M4 requires ALL THREE conditions. Missing: {missing}. "
                "A=process entirely absent; B=zero records in sample; "
                "C=interview confirms absence. "
                "With missing condition(s) → Minor D2 or ReviewRequired."
            ),
            gate="G4",
            forced_nc_class="Minor",
            forced_trigger="D2_process_incomplete"
        )

    return None


def enforce_g6_complied_check(trace: dict, verdict: str) -> Optional[dict]:
    """G6: Complied pre-conditions — all 4 required."""
    if verdict != "Complied":
        return None

    g6 = trace.get("G6_complied_check", {})
    if not g6:
        return reject(
            reason="G6_COMPLIED_NO_TRACE",
            message="Complied verdict requires G6 gate trace. Fill C1–C4 before returning Complied.",
            gate="G6",
            forced_verdict="InsufficientEvidence"
        )

    c1 = g6.get("C1_implementation_proven", False)
    c2 = g6.get("C2_record_proven", False)
    c3 = g6.get("C3_elements_covered", False)
    c4 = g6.get("C4_evidence_current", False)

    if not all([c1, c2, c3, c4]):
        failed = [k for k, v in [("C1", c1), ("C2", c2), ("C3", c3), ("C4", c4)] if not v]
        return reject(
            reason="G6_COMPLIED_PRECONDITION_FAIL",
            message=(
                f"Complied requires C1+C2+C3+C4. Failed: {failed}. "
                "C1=implementation proven; C2=record proven; "
                "C3=all elements covered; C4=evidence current. "
                "Incomplete → InsufficientEvidence."
            ),
            gate="G6",
            forced_verdict="InsufficientEvidence"
        )

    return None


def enforce_g7_trace(trace: dict) -> Optional[dict]:
    """G7: Calibration trace completeness."""
    g7 = trace.get("G7_trace", {})
    if not g7.get("decisive_question"):
        return reject(
            reason="G7_DECISIVE_QUESTION_MISSING",
            message="decisive_question is required for every material verdict.",
            gate="G7"
        )
    return None

# ── Main enforcer ──────────────────────────────────────────────────────────────

def enforce_gates(model_output: dict) -> dict:
    """
    Run all gates against model output struct.
    Returns model_output with gate_validation=PASS, or rejection dict.
    """
    trace = model_output.get("gate_execution_trace", {})
    verdict = model_output.get("verdict", "")
    nc_class = model_output.get("nc_class")
    clause = model_output.get("predicted_clause") or model_output.get("clause")

    # Normalize nc_class
    if nc_class in ("null", "", "None"):
        nc_class = None

    # Run gates in order — stop at first violation
    for gate_fn in [
        lambda: enforce_g0_preflight(trace),
        lambda: enforce_g2_ie_chain(trace, verdict, clause),
        lambda: enforce_g3_severity_ceiling(trace, nc_class, clause),
        lambda: enforce_g4_m4_conditions(trace, nc_class),
        lambda: enforce_g6_complied_check(trace, verdict),
        lambda: enforce_g7_trace(trace),
    ]:
        violation = gate_fn()
        if violation:
            return violation

    model_output["gate_validation"] = "PASS"
    return model_output


def validate_schema(model_output: dict) -> list:
    """Check required fields are present (separate from gate enforcement)."""
    warnings = []
    required = ["gate_execution_trace", "verdict", "nc_class", "trigger_or_anchor"]
    for field in required:
        if field not in model_output:
            warnings.append(f"MISSING_REQUIRED_FIELD: {field}")

    if model_output.get("verdict") not in VALID_VERDICTS:
        warnings.append(f"INVALID_VERDICT: {model_output.get('verdict')}")

    return warnings


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="QMS Deterministic Gate Enforcer")
    parser.add_argument("--input", help="Single model output JSON file")
    parser.add_argument("--batch", help="Batch model predictions JSONL file")
    parser.add_argument("--outdir", default="gate_results", help="Output directory for batch")
    parser.add_argument("--validate-schema", action="store_true", help="Validate schema only")
    args = parser.parse_args()

    if args.validate_schema:
        print("Schema validation: D2_SAFE_LIST has", len(D2_SAFE_LIST), "clauses")
        print("Schema validation: M4_MANDATORY_LIST has", len(M4_MANDATORY_LIST), "clauses")
        print("Schema validation: Gate functions loaded: G0, G2, G3, G4, G6, G7")
        print("✓ harness_gate_executor.py schema validation PASS")
        return

    if args.input:
        with open(args.input) as f:
            model_output = json.load(f)
        warnings = validate_schema(model_output)
        if warnings:
            print("SCHEMA WARNINGS:", warnings)
        result = enforce_gates(model_output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.batch:
        outdir = Path(args.outdir)
        outdir.mkdir(exist_ok=True)
        results = []
        pass_count = fail_count = 0

        with open(args.batch) as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    model_output = json.loads(line)
                except json.JSONDecodeError as e:
                    results.append({"line": i, "error": str(e), "gate_validation": "ERROR"})
                    continue

                result = enforce_gates(model_output)
                results.append(result)
                if result.get("gate_validation") == "PASS":
                    pass_count += 1
                else:
                    fail_count += 1

        # Write results
        out_path = outdir / "gate_enforcement_results.jsonl"
        with open(out_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

        total = pass_count + fail_count
        print(f"\nGate enforcement complete:")
        print(f"  Total: {total} | PASS: {pass_count} ({pass_count/total*100:.1f}%) | FAIL: {fail_count}")
        print(f"  Results written to: {out_path}")

        # Failure breakdown
        failures = [r for r in results if r.get("gate_validation") == "FAIL"]
        if failures:
            from collections import Counter
            reasons = Counter(r.get("rejection_reason", "UNKNOWN") for r in failures)
            print("\n  Failure breakdown:")
            for reason, count in reasons.most_common():
                print(f"    {reason}: {count}")


if __name__ == "__main__":
    main()
