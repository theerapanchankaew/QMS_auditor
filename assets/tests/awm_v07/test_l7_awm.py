"""L7 Conditional Qualifier Gate v2 inside the Audit World Model:
  * aias_awm/qualifiers.py is a parity copy of scripts/conditional_qualifiers.py;
  * l7_inputs() reads the organization's determination only from explicit
    evidence metadata (fail-safe defaults);
  * GateTraceDeriver emits trace["L7_conditional_qualifier"] and follows the
    route; the real harness (gate "L7") re-evaluates it;
  * end to end through AuditWorldRuntime with real corpus requirement records.

Run: PYTHONPATH="scripts/awm_runtime;scripts" python -m pytest assets/tests/awm_v07/test_l7_awm.py -q
"""
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import conditional_qualifiers as cq
from aias_awm import qualifiers as aq
from aias_awm.adapters.production_harness import ProductionHarnessAdapter
from aias_awm.control.gate_trace_deriver import GateTraceDeriver
from aias_awm.domain.models import (
    AtomicRequirement, AuditCase, EpistemicState, EvidenceExpectation, EvidenceItem,
    RequirementAssessment, WorldSnapshot,
)
from aias_awm.persistence import Database
from aias_awm.runtime import AuditWorldRuntime
from requirement_profile_loader import load_requirement_records

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)
HARNESS_PATH = Path(__file__).resolve().parents[3] / "scripts" / "harness_gate_executor.py"


def harness():
    return ProductionHarnessAdapter(str(HARNESS_PATH))


# --- parity with scripts/conditional_qualifiers.py ------------------------

def test_vocabulary_parity():
    assert aq.PHRASE_FAMILY == cq.PHRASE_FAMILY
    for text in ("as appropriate; as applicable (d)", "where relevant", "take appropriate action", "to the extent\nnecessary", None, ""):
        assert aq.phrases_in(text) == [f["phrase"] for f in cq.find_qualifiers(text or "")], text


def test_l7_route_parity_over_every_input_combination():
    for fam, ev, det, just, a3 in itertools.product("ABC", (True, False), cq.DETERMINATIONS, (True, False), cq.A3_EFFECTS):
        kw = dict(condition_evidenced=ev, determination=det, justification=just, a3_effect=a3)
        assert aq.l7_route(fam, **kw)["route"] == cq.l7_route(fam, **kw)["route"], (fam, kw)


def test_combine_and_section_parity():
    for routes in itertools.chain(itertools.combinations(aq.ROUTE_PRIORITY, 1), itertools.combinations(aq.ROUTE_PRIORITY, 2)):
        assert aq.combine_routes(list(routes)) == cq.combine_routes(list(routes))
    for phrases, ev, det in itertools.product(
        (["as applicable"], ["as appropriate"], ["to the extent necessary"], ["as appropriate", "as applicable"]),
        (True, False), cq.DETERMINATIONS,
    ):
        sec = {"phrases": phrases, "condition_evidenced": ev, "determination": det, "justification": True, "a3_effect": "none"}
        assert aq.l7_from_section(sec)["route"] == cq.l7_from_trace(sec)["route"]


# --- l7_inputs: determination only from explicit metadata -----------------

def ev(eid, etype="document", state=EpistemicState.VERIFIED, **meta):
    return EvidenceItem(
        evidence_id=eid, organization_id="ORG-L7", audit_case_id="CASE-L7", process_id="P1",
        evidence_type=etype, assertion="x", epistemic_state=state,
        related_requirement_ids=["AR-8.6-E02"], metadata=meta,
    )


def test_defaults_are_fail_safe():
    i = aq.l7_inputs([])
    assert i == {"condition_evidenced": False, "determination": "none", "justification": False,
                 "a3_effect": "unknown", "determination_conflict": False}


def test_determination_item_is_not_activity_evidence():
    i = aq.l7_inputs([ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="none")])
    assert i["determination"] == "not_applicable" and i["justification"] is True and i["a3_effect"] == "none"
    assert i["condition_evidenced"] is False


def test_any_other_active_evidence_counts_as_the_activity_existing():
    assert aq.l7_inputs([ev("E1", "observation")])["condition_evidenced"] is True
    assert aq.l7_inputs([ev("E1", "observation", state=EpistemicState.INVALID)])["condition_evidenced"] is False
    assert aq.l7_inputs([ev("E1", "interview", condition_applies=False)])["condition_evidenced"] is False


def test_conflicting_determinations_are_flagged():
    i = aq.l7_inputs([ev("D1", org_determination="applicable"), ev("D2", org_determination="not_applicable")])
    assert i["determination_conflict"] is True and i["determination"] == "none"


def test_applicability_claim_is_read_only_without_a_recorded_determination():
    assert aq.l7_inputs([], "NOT_APPLICABLE")["determination"] == "not_applicable"
    assert aq.l7_inputs([ev("D1", org_determination="applicable")], "NOT_APPLICABLE")["determination"] == "applicable"


def test_a3_effect_worst_case_wins():
    i = aq.l7_inputs([
        ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="none"),
        ev("D2", org_determination="not_applicable", na_justification=True, a3_effect="affects"),
    ])
    assert i["a3_effect"] == "affects"


# --- GateTraceDeriver ------------------------------------------------------

def requirement(rid="AR-8.6-E02", clause="8.6", qualifier="as applicable"):
    return AtomicRequirement(
        requirement_id=rid, standard_id="ISO 9001:2026", clause=clause, subject="organization", obligation="ensure",
        object="release approval", qualifier=qualifier, semantic_category="AMBIGUOUS",
        evidence_expectations=[EvidenceExpectation(evidence_type="observation", minimum_strength="implemented", mandatory=True)],
        version="t",
    )


def assessment(state, applicability="APPLICABLE", rid="AR-8.6-E02", **kw):
    return RequirementAssessment(
        assessment_id="RA-1", audit_case_id="CASE-L7", requirement_id=rid, applicability=applicability,
        state=state, updated_at=NOW, **kw,
    )


def snapshot():
    return WorldSnapshot(snapshot_id="S1", organization_id="ORG-L7", as_of=NOW, requirement_states=[],
                         source_manifest_hash="REAL-SHA256", rule_pack_hash="R", created_from_event_seq=0)


def derive(req, a, evidence=()):
    return GateTraceDeriver().derive(assessment=a, requirement=req, evidence_items=list(evidence), snapshot=snapshot())


def test_undetermined_family_a_derives_ofi_and_passes_the_real_harness():
    c = derive(requirement(), assessment("INSUFFICIENT_EVIDENCE"))
    assert c["verdict"] == "OFI" and c["derivation_provenance"]["l7_route"] == "OFI_STOP"
    assert c["gate_execution_trace"]["L7_conditional_qualifier"]["phrases"] == ["as applicable"]
    r = harness().enforce(c, {})
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "OFI_STOP", r


def test_justified_not_applicable_derives_complied_without_g6():
    d = ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="none")
    c = derive(requirement(), assessment("NOT_APPLICABLE", applicability="NOT_APPLICABLE"), [d])
    assert c["verdict"] == "Complied" and c["gate_execution_trace"]["G6_complied_check"] == {}
    r = harness().enforce(c, {})
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "COMPLIED_STOP", r


@pytest.mark.parametrize("a3,route", [("affects", "ROUTE_4_3"), (None, "REVIEW_REQUIRED")])
def test_not_applicable_that_cannot_be_cleared_by_a3_is_review_required(a3, route):
    meta = {"org_determination": "not_applicable", "na_justification": True}
    if a3:
        meta["a3_effect"] = a3
    c = derive(requirement(), assessment("NOT_APPLICABLE", applicability="NOT_APPLICABLE"), [ev("D1", **meta)])
    assert c["verdict"] == "ReviewRequired" and c["derivation_provenance"]["l7_route"] == route
    assert harness().enforce(c, {})["gate_validation"] == "PASS"


def test_not_applicable_without_justification_is_ofi():
    d = ev("D1", org_determination="not_applicable", a3_effect="none")
    c = derive(requirement(), assessment("NOT_APPLICABLE", applicability="NOT_APPLICABLE"), [d])
    assert c["verdict"] == "OFI" and harness().enforce(c, {})["gate_validation"] == "PASS"


def test_family_b_is_never_closed_as_not_applicable():
    req = requirement("AR-8.3.5-E01", "8.3.5", "as appropriate")
    c = derive(req, assessment("INSUFFICIENT_EVIDENCE", rid="AR-8.3.5-E01"))
    assert c["verdict"] == "InsufficientEvidence" and c["derivation_provenance"]["l7_route"] == "L8"
    # an applicability claim on 'as appropriate' must not become OUT_OF_SCOPE / Complied
    c2 = derive(req, assessment("NOT_APPLICABLE", applicability="NOT_APPLICABLE", rid="AR-8.3.5-E01"))
    assert c2["verdict"] == "ReviewRequired"


def test_evidence_that_the_activity_exists_overrides_the_not_applicable_claim():
    act = ev("E1", "observation")
    c = derive(requirement(), assessment("NOT_APPLICABLE", applicability="NOT_APPLICABLE"), [act])
    assert c["derivation_provenance"]["l7_route"] == "L8" and c["verdict"] == "ReviewRequired"


def test_breach_on_a_conditional_element_with_activity_evidence_stays_nc_and_passes():
    act = ev("E1", "record", proves_breach=True)
    c = derive(requirement(), assessment("BREACH_PROVEN", breach_proven=True, negative_evidence_ids=["E1"]), [act])
    assert c["verdict"] == "Noncomplied" and c["derivation_provenance"]["l7_route"] == "L8"
    r = harness().enforce(c, {})
    assert r["gate_validation"] == "PASS" and r["l7_route"] == "L8", r


def test_requirement_without_qualifier_is_untouched():
    c = derive(requirement("AR-6.1.3-E02", "6.1.3", None), assessment("INSUFFICIENT_EVIDENCE", rid="AR-6.1.3-E02"))
    assert "L7_conditional_qualifier" not in c["gate_execution_trace"]
    assert c["verdict"] == "InsufficientEvidence" and c["derivation_provenance"]["l7_route"] is None


# --- end to end: real corpus record -> runtime -> real harness -------------

def runtime():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    rt = AuditWorldRuntime(db, harness(), source_manifest_hash="REAL-SHA256-L7", rule_pack_hash="RULE1")
    rt.create_case(AuditCase(audit_case_id="CASE-L7", organization_id="ORG-L7", standard_ids=["ISO9001-2026"],
                             audit_type="document_review", scope={}, created_at=NOW))
    rec = load_requirement_records(["AR-8.6-E02"])[0]
    assert rec["qualifier"] == "as applicable"
    rt.register_requirement(AtomicRequirement(**rec))
    return rt


def settle_another_requirement(rt):
    """WG6 (unchanged, fail-closed) needs at least one APPLICABLE, resolved
    requirement in the snapshot: an all-not-applicable case is never
    decision-ready. Real audits always have one; add a plain satisfied one."""
    rt.register_requirement(requirement("AR-6.1.3-E02", "6.1.3", None))
    rt.ingest_evidence(EvidenceItem(
        evidence_id="OK1", organization_id="ORG-L7", audit_case_id="CASE-L7", process_id="P1",
        evidence_type="observation", assertion="x", epistemic_state=EpistemicState.VERIFIED,
        related_requirement_ids=["AR-6.1.3-E02"], metadata={},
    ))
    return ["AR-8.6-E02", "AR-6.1.3-E02"]


def test_end_to_end_justified_not_applicable_reaches_the_harness_as_complied():
    rt = runtime()
    rt.ingest_evidence(ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="none"))
    assert rt.reason("CASE-L7", settle_another_requirement(rt))["decision_ready"] is True
    d = rt.make_decision_for_requirement("CASE-L7", "AR-8.6-E02")
    assert d["gate_validation"] == "PASS" and d["verdict"] == "Complied" and d["l7_route"] == "COMPLIED_STOP", d
    json.dumps(d)


def test_end_to_end_a3_not_met_is_review_required_not_complied():
    rt = runtime()
    rt.ingest_evidence(ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="affects"))
    rt.reason("CASE-L7", settle_another_requirement(rt))
    d = rt.make_decision_for_requirement("CASE-L7", "AR-8.6-E02")
    assert d["gate_validation"] == "PASS" and d["verdict"] == "ReviewRequired" and d["l7_route"] == "ROUTE_4_3", d


def test_end_to_end_unjustified_not_applicable_is_ofi():
    rt = runtime()
    rt.ingest_evidence(ev("D1", org_determination="not_applicable", a3_effect="none"))
    rt.reason("CASE-L7", settle_another_requirement(rt))
    d = rt.make_decision_for_requirement("CASE-L7", "AR-8.6-E02")
    assert d["gate_validation"] == "PASS" and d["verdict"] == "OFI" and d["l7_route"] == "OFI_STOP", d


def test_end_to_end_all_not_applicable_snapshot_is_not_decision_ready_by_wg6():
    """Pre-existing WG6 behaviour, kept: with no APPLICABLE requirement in the
    snapshot nothing is 'material', so the world is not decision-ready."""
    rt = runtime()
    rt.ingest_evidence(ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="none"))
    rt.reason("CASE-L7", ["AR-8.6-E02"])
    d = rt.make_decision_for_requirement("CASE-L7", "AR-8.6-E02")
    assert d["status"] == "WORLD_NOT_DECISION_READY" and "gate_validation" not in d


def test_end_to_end_activity_evidence_beats_the_not_applicable_claim():
    rt = runtime()
    rt.ingest_evidence(ev("D1", org_determination="not_applicable", na_justification=True, a3_effect="none"))
    rt.ingest_evidence(ev("E1", "observation"))
    res = rt.reason("CASE-L7", ["AR-8.6-E02"])
    assert res["assessments"][0]["applicability"] == "APPLICABLE"  # not short-circuited as N/A
    assert res["assessments"][0]["state"] != "NOT_APPLICABLE"


def test_loader_rejects_unknown_requirements():
    with pytest.raises(KeyError):
        load_requirement_records(["AR-8.6-E99"])
    with pytest.raises(KeyError):
        load_requirement_records(["AR-99.9-E01"])
