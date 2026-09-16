#!/usr/bin/env python3
"""
run_regression_suite.py — QMS Auditor v1.1
Run hardened skill regression checks.

v1.1 changes (harness audit remediation):
  - Adds behavioral smoke tests (D5 gap fix): runs evaluate_model_predictions.py
    against pre-built gold/pred fixtures to verify actual scoring logic.
  - Pass condition: behavioral-smoke-pred-pass must score >= threshold.
  - Regression condition: behavioral-smoke-pred-fail must score below threshold AND
    produce the expected failure_layer signatures.
  - Structural checks unchanged (file_exists + test_file_parse).

Usage:
  python scripts/run_regression_suite.py --skill-root . --outdir regression_results
"""
import argparse, json, subprocess, sys, csv
from pathlib import Path

BEHAVIORAL_THRESHOLD = 0.90   # composite_verdict_nc macro_f1 must be >= this for pass fixture
REGRESSION_CEILING   = 0.80   # fail fixture must score < this (otherwise failure injection failed)

# Expected failure layers in the fail fixture (at least these must appear)
EXPECTED_FAIL_LAYERS = {
    "L7_conditional_qualifier",
    "L10_L11_severity_counterfactual",
    "L8_breach_test_FP",
}


def load_jsonl(p: Path):
    rows = []
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_csv_summary(csv_path: Path) -> dict:
    """Load metric_summary.csv → {target: {accuracy, macro_f1, ...}}"""
    result = {}
    if not csv_path.exists():
        return result
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["target"]] = {k: float(v) for k, v in row.items() if k != "target"}
    return result


def load_failure_layer_breakdown(csv_path: Path) -> dict:
    """Load failure_layer_breakdown.csv → {layer: count}"""
    result = {}
    if not csv_path.exists():
        return result
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result[row["failure_layer"]] = int(row["count"])
    return result


def run_evaluator(skill_root: Path, gold: Path, pred: Path, outdir: Path) -> dict | None:
    """Run evaluate_model_predictions.py and return parsed JSON result."""
    script = skill_root / "scripts" / "evaluate_model_predictions.py"
    if not script.exists():
        return None
    result = subprocess.run(
        [sys.executable, str(script),
         "--gold", str(gold), "--pred", str(pred), "--outdir", str(outdir)],
        capture_output=True, text=True
    )
    try:
        # stdout is the JSON summary; stderr contains warnings/assertions
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"error": result.stdout + result.stderr}


def main():
    p = argparse.ArgumentParser(description="Run QMS hardened skill regression smoke checks v1.1")
    p.add_argument("--skill-root", default=".")
    p.add_argument("--outdir",     default="regression_results")
    args   = p.parse_args()
    root   = Path(args.skill_root)
    out    = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    checks = []

    # ──────────────────────────────────────────────────────────────────────────
    # GROUP 1: Structural checks — required harness files exist
    # ──────────────────────────────────────────────────────────────────────────
    required = [
        "references/29-harnesscard-qms-auditor.md",
        "references/30-control-layer-contract.md",
        "references/31-agency-action-surface.md",
        "references/32-context-window-management.md",
        "references/33-runtime-recovery-and-repeatability.md",
        "references/34-evaluation-harness-protocol.md",
        "references/35-robustness-test-suite.md",
        "assets/templates/context-ledger-template.json",
        "assets/templates/decision-trace-template.json",
        "assets/templates/model-predictions-schema.json",
        "scripts/validate_context_ledger.py",
        "scripts/validate_decision_trace.py",
        "scripts/generate_harnesscard.py",
        # v6.1 Audit World Model extension
        "references/51-audit-world-model-v2.md",
        "references/52-imagination-engine-v1.md",
        "references/53-audit-policy-engine-v1.md",
        "references/54-process-enforcer-binding-v1.md",
        "references/55-offline-audit-learning-governance-v1.md",
        "references/56-dreamer4-design-transfer-note-v1.md",
        "scripts/audit_world_model.py",
        "scripts/imagination_engine.py",
        "scripts/process_enforcer.py",
        "assets/templates/audit-state-v2.json",
        "assets/tests/world-model-v2-actions.json",
        # behavioral fixtures
        "assets/tests/behavioral-smoke-gold.jsonl",
        "assets/tests/behavioral-smoke-pred-pass.jsonl",
        "assets/tests/behavioral-smoke-pred-fail.jsonl",
    ]
    for r in required:
        checks.append({
            "group":  "structural",
            "check":  "file_exists",
            "target": r,
            "passed": (root / r).exists(),
        })

    # ──────────────────────────────────────────────────────────────────────────
    # GROUP 2: Test file parse — all test JSONL are valid + non-empty
    # ──────────────────────────────────────────────────────────────────────────
    test_dir     = root / "assets" / "tests"
    total_cases  = 0
    for pth in sorted(test_dir.glob("*.jsonl")):
        rows = load_jsonl(pth)
        total_cases += len(rows)
        checks.append({
            "group":      "structural",
            "check":      "test_file_parse",
            "target":     str(pth.relative_to(root)),
            "passed":     len(rows) > 0,
            "case_count": len(rows),
        })

    # ──────────────────────────────────────────────────────────────────────────
    # GROUP 3: Context ledger and decision trace schema validation
    # ──────────────────────────────────────────────────────────────────────────
    for script_name, template_path in [
        ("validate_context_ledger.py",  "assets/templates/context-ledger-template.json"),
        ("validate_decision_trace.py",  "assets/templates/decision-trace-template.json"),
    ]:
        script   = root / "scripts" / script_name
        template = root / template_path
        if script.exists() and template.exists():
            result = subprocess.run(
                [sys.executable, str(script), str(template)],
                capture_output=True, text=True
            )
            try:
                r = json.loads(result.stdout)
                passed = r.get("status") == "passed"
            except Exception:
                passed = False
            checks.append({
                "group":  "schema_validation",
                "check":  f"template_valid:{script_name}",
                "target": template_path,
                "passed": passed,
            })
        else:
            checks.append({
                "group":  "schema_validation",
                "check":  f"template_valid:{script_name}",
                "target": template_path,
                "passed": False,
                "note":   "script or template missing",
            })

    # ──────────────────────────────────────────────────────────────────────────
    # GROUP 4 (NEW): Behavioral smoke tests — scoring logic validation
    # ──────────────────────────────────────────────────────────────────────────
    gold_path       = root / "assets" / "tests" / "behavioral-smoke-gold.jsonl"
    pred_pass_path  = root / "assets" / "tests" / "behavioral-smoke-pred-pass.jsonl"
    pred_fail_path  = root / "assets" / "tests" / "behavioral-smoke-pred-fail.jsonl"
    eval_pass_dir   = out / "behavioral_pass"
    eval_fail_dir   = out / "behavioral_fail"

    if gold_path.exists() and pred_pass_path.exists():
        # 4a: Pass fixture — composite macro F1 must be >= BEHAVIORAL_THRESHOLD
        run_result = run_evaluator(root, gold_path, pred_pass_path, eval_pass_dir)
        if run_result and "error" not in run_result:
            summary = load_csv_summary(eval_pass_dir / "metric_summary.csv")
            composite_f1 = summary.get("composite_verdict_nc", {}).get("macro_f1", 0.0)
            passed = composite_f1 >= BEHAVIORAL_THRESHOLD
            checks.append({
                "group":          "behavioral",
                "check":          "pass_fixture_composite_f1",
                "target":         "behavioral-smoke-pred-pass.jsonl",
                "passed":         passed,
                "composite_f1":   round(composite_f1, 4),
                "threshold":      BEHAVIORAL_THRESHOLD,
                "note":           f"composite_verdict_nc macro_f1 = {composite_f1:.4f} (need >= {BEHAVIORAL_THRESHOLD})",
            })
        else:
            checks.append({
                "group":  "behavioral",
                "check":  "pass_fixture_composite_f1",
                "target": "behavioral-smoke-pred-pass.jsonl",
                "passed": False,
                "note":   f"evaluator error: {run_result}",
            })
    else:
        checks.append({
            "group":  "behavioral",
            "check":  "pass_fixture_composite_f1",
            "target": "behavioral-smoke-pred-pass.jsonl",
            "passed": False,
            "note":   "fixture files missing",
        })

    if gold_path.exists() and pred_fail_path.exists():
        # 4b: Fail fixture — composite F1 must be < REGRESSION_CEILING
        run_result = run_evaluator(root, gold_path, pred_fail_path, eval_fail_dir)
        if run_result and "error" not in run_result:
            summary    = load_csv_summary(eval_fail_dir / "metric_summary.csv")
            layers     = load_failure_layer_breakdown(eval_fail_dir / "failure_layer_breakdown.csv")
            composite  = summary.get("composite_verdict_nc", {}).get("macro_f1", 1.0)
            score_low  = composite < REGRESSION_CEILING

            # Check that expected failure layers are present
            found_layers   = set(layers.keys())
            missing_layers = EXPECTED_FAIL_LAYERS - found_layers
            layers_ok      = len(missing_layers) == 0

            passed = score_low and layers_ok
            checks.append({
                "group":           "behavioral",
                "check":           "fail_fixture_regression_detection",
                "target":          "behavioral-smoke-pred-fail.jsonl",
                "passed":          passed,
                "composite_f1":    round(composite, 4),
                "ceiling":         REGRESSION_CEILING,
                "found_layers":    sorted(found_layers),
                "missing_layers":  sorted(missing_layers),
                "note": (
                    f"composite_f1={composite:.4f} (need < {REGRESSION_CEILING}); "
                    f"layers detected={sorted(found_layers)}; "
                    f"missing={sorted(missing_layers)}"
                ),
            })
        else:
            checks.append({
                "group":  "behavioral",
                "check":  "fail_fixture_regression_detection",
                "target": "behavioral-smoke-pred-fail.jsonl",
                "passed": False,
                "note":   f"evaluator error: {run_result}",
            })
    else:
        checks.append({
            "group":  "behavioral",
            "check":  "fail_fixture_regression_detection",
            "target": "behavioral-smoke-pred-fail.jsonl",
            "passed": False,
            "note":   "fixture files missing",
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 4c: Label leakage — prepare_model_performance_inputs must strip leak keys
    # ──────────────────────────────────────────────────────────────────────────
    leak_test_src = root / "assets" / "tests" / "label-leakage-regression.jsonl"
    prep_script   = root / "scripts" / "prepare_model_performance_inputs.py"
    if leak_test_src.exists() and prep_script.exists():
        leaky_input = out / "leaky_input_tmp.jsonl"
        # Build a minimal leaky JSONL for testing
        leaky_input.write_text(
            '{"case_id":"LEAK-TEST-001","scenario":"no release verification",'
            '"expected_verdict":"Noncomplied","expected_nc_class":"Major","clause":"8.6"}\n',
            encoding="utf-8"
        )
        sanitize_out = out / "sanitize_test"
        result = subprocess.run(
            [sys.executable, str(prep_script),
             "--source", str(leaky_input), "--outdir", str(sanitize_out)],
            capture_output=True, text=True
        )
        sanitized_file = sanitize_out / "qms_test_inputs_sanitized_no_labels.jsonl"
        leak_found = False
        if sanitized_file.exists():
            for line in sanitized_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    if "expected_verdict" in row or "expected_nc_class" in row:
                        leak_found = True
        checks.append({
            "group":  "behavioral",
            "check":  "label_leakage_sanitization",
            "target": "prepare_model_performance_inputs.py",
            "passed": not leak_found and sanitized_file.exists(),
            "note":   "leak keys removed from sanitized output" if not leak_found else "LEAK DETECTED",
        })
    else:
        checks.append({
            "group":  "behavioral",
            "check":  "label_leakage_sanitization",
            "target": "prepare_model_performance_inputs.py",
            "passed": False,
            "note":   "source or script missing",
        })

    # ──────────────────────────────────────────────────────────────────────────
    # GROUP 5: Audit World Model safety boundary smoke checks
    # ──────────────────────────────────────────────────────────────────────────
    wm_script = root / "scripts" / "audit_world_model.py"
    wm_state = root / "assets" / "templates" / "audit-state-v2.json"
    if wm_script.exists() and wm_state.exists():
        action_path = out / "wm_action.json"
        wm_out = out / "wm_simulated_state.json"
        action_path.write_text('{"action_type":"request_document_or_record","target":"effectiveness evaluation"}', encoding="utf-8")
        r = subprocess.run([sys.executable, str(wm_script), "--state", str(wm_state), "--action", str(action_path), "--output", str(wm_out)], capture_output=True, text=True)
        ok = False
        if r.returncode == 0 and wm_out.exists():
            d = json.loads(wm_out.read_text(encoding="utf-8"))
            ok = d.get("simulation") is True and d.get("epistemic_class") == "prediction_only" and d.get("evidence_status") == "not_audit_evidence" and not any(k in d for k in ("verdict","nc_class","trigger_or_anchor"))
        checks.append({"group":"world_model_safety","check":"simulation_not_evidence","target":"audit_world_model.py","passed":ok})
    else:
        checks.append({"group":"world_model_safety","check":"simulation_not_evidence","target":"audit_world_model.py","passed":False})

    pe_script = root / "scripts" / "process_enforcer.py"
    if pe_script.exists():
        req = out / "pe_transition.json"; res = out / "pe_transition_result.json"
        req.write_text('{"current_state":"S3_MAPPED","requested_state":"S4_SUFFICIENCY","artifact_epistemic_class":"prediction_only"}', encoding="utf-8")
        r = subprocess.run([sys.executable, str(pe_script), "--input", str(req), "--output", str(res)], capture_output=True, text=True)
        ok = False
        if res.exists():
            d = json.loads(res.read_text(encoding="utf-8"))
            ok = r.returncode != 0 and d.get("allowed") is False and d.get("code") == "PREDICTION_CANNOT_ADVANCE_ASSURANCE"
        checks.append({"group":"world_model_safety","check":"prediction_cannot_advance_assurance","target":"process_enforcer.py","passed":ok})
    else:
        checks.append({"group":"world_model_safety","check":"prediction_cannot_advance_assurance","target":"process_enforcer.py","passed":False})

    # ──────────────────────────────────────────────────────────────────────────
    # GROUP 6: Audit World Model coherence and detour checks
    # ──────────────────────────────────────────────────────────────────────────
    coherence_script = root / "scripts" / "world_model_coherence.py"
    coherence_cases = root / "assets" / "tests" / "world-model-coherence-cases.json"
    if coherence_script.exists() and coherence_cases.exists():
        result_path = out / "world_model_coherence.json"
        r = subprocess.run([sys.executable, str(coherence_script), "--cases", str(coherence_cases), "--output", str(result_path)], capture_output=True, text=True)
        ok = r.returncode == 0 and result_path.exists()
        note = ""
        if result_path.exists():
            d=json.loads(result_path.read_text(encoding="utf-8")); note=json.dumps(d.get("summary",{}), sort_keys=True)
        checks.append({"group":"world_model_coherence","check":"compression_and_distinction","target":"world_model_coherence.py","passed":ok,"note":note})
    else:
        checks.append({"group":"world_model_coherence","check":"compression_and_distinction","target":"world_model_coherence.py","passed":False,"note":"script or cases missing"})

    detour_script = root / "scripts" / "audit_detour_test.py"
    detour_cases = root / "assets" / "tests" / "audit-detour-cases.json"
    if detour_script.exists() and detour_cases.exists():
        result_path = out / "audit_detour.json"
        r = subprocess.run([sys.executable, str(detour_script), "--cases", str(detour_cases), "--output", str(result_path)], capture_output=True, text=True)
        ok = r.returncode == 0 and result_path.exists()
        note = ""
        if result_path.exists():
            d=json.loads(result_path.read_text(encoding="utf-8")); note=json.dumps(d.get("summary",{}), sort_keys=True)
        checks.append({"group":"world_model_coherence","check":"detour_robustness","target":"audit_detour_test.py","passed":ok,"note":note})
    else:
        checks.append({"group":"world_model_coherence","check":"detour_robustness","target":"audit_detour_test.py","passed":False,"note":"script or cases missing"})

    dynamics_script = root / "scripts" / "audit_dynamics_contract.py"
    dynamics_case = root / "assets" / "tests" / "audit-dynamics-contract-valid.json"
    if dynamics_script.exists() and dynamics_case.exists():
        result_path = out / "audit_dynamics_contract.json"
        r = subprocess.run([sys.executable, str(dynamics_script), "--input", str(dynamics_case), "--output", str(result_path)], capture_output=True, text=True)
        ok = r.returncode == 0 and result_path.exists() and json.loads(result_path.read_text(encoding="utf-8")).get("valid") is True
        checks.append({"group":"world_model_coherence","check":"dynamics_authority_contract","target":"audit_dynamics_contract.py","passed":ok})
    else:
        checks.append({"group":"world_model_coherence","check":"dynamics_authority_contract","target":"audit_dynamics_contract.py","passed":False})

    # ──────────────────────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────────────────────
    pass_count = sum(1 for c in checks if c.get("passed"))
    status     = "passed" if pass_count == len(checks) else "failed"

    # Group breakdown
    groups: dict[str, dict] = {}
    for c in checks:
        g = c.get("group", "other")
        groups.setdefault(g, {"total": 0, "passed": 0})
        groups[g]["total"]  += 1
        groups[g]["passed"] += int(bool(c.get("passed")))

    report  = "# QMS Hardened Regression Report v1.1\n\n"
    report += f"- Status: **{status}**\n"
    report += f"- Total checks passed: {pass_count}/{len(checks)}\n"
    report += f"- Test cases loaded: {total_cases}\n\n"
    report += "## Group summary\n\n"
    report += "| Group | Passed | Total |\n|---|---:|---:|\n"
    for g, counts in groups.items():
        report += f"| {g} | {counts['passed']} | {counts['total']} |\n"
    report += "\n## All checks\n\n"
    report += "| Group | Check | Target | Result | Note |\n|---|---|---|---|---|\n"
    for c in checks:
        note = c.get("note") or c.get("composite_f1") or ""
        report += (f"| {c.get('group','')} | {c['check']} | `{c['target']}` "
                   f"| {'PASS' if c.get('passed') else 'FAIL'} | {note} |\n")

    (out / "regression_report.md").write_text(report, encoding="utf-8")
    (out / "regression_results.json").write_text(
        json.dumps({"status": status, "checks": checks,
                    "total_cases": total_cases, "groups": groups}, indent=2),
        encoding="utf-8"
    )
    print(json.dumps({
        "status":     status,
        "report":     str(out / "regression_report.md"),
        "checks":     len(checks),
        "passed":     pass_count,
        "groups":     groups,
    }, indent=2))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
