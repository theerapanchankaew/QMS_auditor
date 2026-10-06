"""The L7 Conditional Qualifier Gate enforced by scripts/harness_gate_executor.py
(gate "L7"). This is the path the OpenWebUI gateway uses: it extracts the
model's gate_execution_trace and runs the harness as a subprocess.

Run:  python -m pytest assets/tests/test_l7_harness_gate.py -q
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import conditional_qualifiers as cq  # noqa: E402
import harness_gate_executor as h  # noqa: E402

HARNESS = ROOT / "scripts" / "harness_gate_executor.py"


def candidate(clause="8.6", verdict="Noncomplied", nc_class="Minor", l7=None, extra_trace=None):
    trace = {
        "G0_preflight": {"closed_source_confirmed": True},
        "G1_linguistic": {"evidence_activity": "VERIFIED"},
        "G7_trace": {"decisive_question": "Is the qualifier condition met?"},
    }
    if l7 is not None:
        trace["L7_conditional_qualifier"] = l7
    trace.update(extra_trace or {})
    return {"predicted_clause": clause, "verdict": verdict, "nc_class": nc_class, "gate_execution_trace": trace}


def run(cand):
    return h.enforce_gates(copy.deepcopy(cand))


UNDETERMINED_A = {"phrases": ["as applicable"], "condition_evidenced": False, "determination": "none"}
JUSTIFIED_NA = {"phrases": ["as applicable"], "condition_evidenced": False, "determination": "not_applicable",
                "justification": True, "a3_effect": "none"}
NA_AFFECTS = {**JUSTIFIED_NA, "a3_effect": "affects"}
NA_UNKNOWN = {k: v for k, v in JUSTIFIED_NA.items() if k != "a3_effect"}
EVIDENCED = {"phrases": ["as applicable"], "condition_evidenced": True, "determination": "none"}


# --- "do not return NC for a conditional clause without running L7" -------

@pytest.mark.parametrize("clause", ["8.6", "7.2", "10.2.1", "8.3.2", "8.3.5", "8.5.3", "8.5.5", "8.5.4"])
def test_nc_on_conditional_clause_without_l7_is_rejected(clause):
    r = run(candidate(clause=clause))
    assert r["gate_validation"] == "FAIL" and r["gate_failed"] == "L7", r
    assert r["rejection_reason"] == "L7_NOT_RUN"
    assert r["forced_overrides"]["forced_verdict"] == "ReviewRequired"


def test_nc_on_non_conditional_clause_needs_no_l7():
    assert run(candidate(clause="6.1.3"))["gate_validation"] == "PASS"


def test_non_nc_verdicts_need_no_l7_section():
    for verdict, nc in (("InsufficientEvidence", None), ("OFI", None), ("ReviewRequired", None)):
        assert run(candidate(verdict=verdict, nc_class=nc))["gate_validation"] == "PASS", verdict


# --- route vs verdict -----------------------------------------------------

def test_undetermined_family_a_cannot_be_nc_forced_to_ofi():
    r = run(candidate(l7=UNDETERMINED_A))
    assert r["gate_failed"] == "L7" and r["rejection_reason"] == "L7_ROUTE_VIOLATION"
    assert r["forced_overrides"] == {"forced_verdict": "OFI", "l7_route": "OFI_STOP"}


def test_undetermined_family_a_as_ofi_passes_and_echoes_route():
    r = run(candidate(verdict="OFI", nc_class=None, l7=UNDETERMINED_A))
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "OFI_STOP"


def test_justified_not_applicable_is_complied_and_skips_g6():
    r = run(candidate(verdict="Complied", nc_class=None, l7=JUSTIFIED_NA))
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "COMPLIED_STOP", r


def test_justified_not_applicable_cannot_be_nc():
    r = run(candidate(l7=JUSTIFIED_NA))
    assert r["rejection_reason"] == "L7_ROUTE_VIOLATION" and r["forced_overrides"]["forced_verdict"] == "Complied"


def test_a3_not_met_routes_to_4_3_and_forbids_complied():
    r = run(candidate(verdict="Complied", nc_class=None, l7=NA_AFFECTS))
    assert r["rejection_reason"] == "L7_ROUTE_VIOLATION"
    assert r["forced_overrides"] == {"forced_verdict": "ReviewRequired", "l7_route": "ROUTE_4_3"}
    assert run(candidate(verdict="ReviewRequired", nc_class=None, l7=NA_AFFECTS))["gate_validation"] == "PASS"


def test_unknown_a3_effect_never_yields_complied():
    r = run(candidate(verdict="Complied", nc_class=None, l7=NA_UNKNOWN))
    assert r["rejection_reason"] == "L7_ROUTE_VIOLATION" and r["forced_overrides"]["l7_route"] == "REVIEW_REQUIRED"


def test_evidence_that_condition_applies_overrides_a_not_applicable_claim():
    l7 = {**JUSTIFIED_NA, "condition_evidenced": True}
    r = run(candidate(l7=l7))  # NC allowed again: route L8
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "L8"


def test_family_b_never_complied_by_not_applicable():
    l7 = {"phrases": ["as appropriate"], "condition_evidenced": False, "determination": "not_applicable",
          "justification": True, "a3_effect": "none"}
    r = run(candidate(clause="8.3.5", verdict="Complied", nc_class=None, l7=l7))
    # L7 imposes no constraint (route L8) but G6 still demands implementation proof
    assert r["gate_failed"] == "G6", r


def test_family_c_undetermined_extent_is_ofi():
    l7 = {"phrases": ["to the extent necessary"], "condition_evidenced": False, "determination": "none"}
    r = run(candidate(clause="8.5.4", l7=l7))
    assert r["rejection_reason"] == "L7_ROUTE_VIOLATION" and r["forced_overrides"]["forced_verdict"] == "OFI"


def test_review_required_is_never_a_l7_violation():
    for l7 in (UNDETERMINED_A, JUSTIFIED_NA, NA_AFFECTS, NA_UNKNOWN):
        assert run(candidate(verdict="ReviewRequired", nc_class=None, l7=l7))["gate_validation"] == "PASS"


def test_models_own_route_claim_is_ignored():
    l7 = {**UNDETERMINED_A, "route": "L8"}
    assert run(candidate(l7=l7))["rejection_reason"] == "L7_ROUTE_VIOLATION"


def test_mixed_family_element_is_never_closed_by_its_applicability_phrase():
    l7 = {"phrases": ["as appropriate", "as applicable"], "condition_evidenced": False, "determination": "none"}
    r = run(candidate(clause="8.4.3", l7=l7))
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "L8"


# --- malformed sections fail closed --------------------------------------

@pytest.mark.parametrize("bad", [
    "text", [], {}, {"phrases": [], "condition_evidenced": False},
    {"phrases": ["as applicable"]},
    {"phrases": ["as applicable"], "condition_evidenced": "no"},
    {"phrases": ["shall ensure"], "condition_evidenced": False},
    {"phrases": ["as applicable"], "condition_evidenced": False, "determination": "maybe"},
    {"phrases": ["as applicable"], "condition_evidenced": False, "a3_effect": "some"},
    {"phrases": ["as applicable"], "condition_evidenced": False, "justification": "yes"},
])
def test_malformed_l7_section_is_rejected(bad):
    r = run(candidate(verdict="OFI", nc_class=None, l7=bad))
    assert r["gate_validation"] == "FAIL" and r["rejection_reason"] == "L7_TRACE_INVALID", r
    assert r["forced_overrides"]["forced_verdict"] == "ReviewRequired"


def test_determination_conflict_routes_to_review():
    l7 = {**UNDETERMINED_A, "determination_conflict": True}
    r = run(candidate(l7=l7))
    assert r["forced_overrides"]["l7_route"] == "REVIEW_REQUIRED"


# --- the paths the gateway and the AWM adapter actually use ---------------

def test_cli_as_run_by_the_gateway(tmp_path):
    f = tmp_path / "trace.json"
    f.write_text(json.dumps(candidate(l7=UNDETERMINED_A)), encoding="utf-8")
    p = subprocess.run([sys.executable, str(HARNESS), "--input", str(f)], capture_output=True, text=True, cwd=tmp_path)
    # the CLI may print a 'SCHEMA WARNINGS' line before the JSON document
    out = json.loads(p.stdout[p.stdout.index("{"):])
    assert out["gate_validation"] == "FAIL" and out["gate_failed"] == "L7", p.stdout + p.stderr


def test_loadable_by_file_path_from_any_directory(tmp_path):
    """ProductionHarnessAdapter loads the harness with importlib from a path;
    its sibling import must work without scripts/ on sys.path."""
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('aias_legacy_harness', r'{HARNESS}')\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "t = {'predicted_clause': '8.6', 'verdict': 'Noncomplied', 'nc_class': 'Minor', 'gate_execution_trace': "
        "{'G0_preflight': {'closed_source_confirmed': True}, 'G7_trace': {'decisive_question': 'q'}}}\n"
        "print(json.dumps(m.enforce_gates(t)))\n"
    )
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=tmp_path)
    assert json.loads(p.stdout[p.stdout.index("{"):])["rejection_reason"] == "L7_NOT_RUN", p.stdout + p.stderr


def test_conditional_clause_set_matches_the_documented_inventory():
    assert cq.is_conditional_clause("8.3") and cq.is_conditional_clause("8.3.4")
    assert not cq.is_conditional_clause("6.1.3") and not cq.is_conditional_clause(None)
    assert len(cq.QUALIFIER_CLAUSES) == 22
