from datetime import datetime, timezone

from fastapi.testclient import TestClient

from aias_awm.adapters.legacy_harness import LegacyAIASHarnessStub
from aias_awm.api import create_app
from aias_awm.domain.models import (
    AuditCase,
    AtomicRequirement,
    EvidenceExpectation,
    EvidenceItem,
    EpistemicState,
    ReasoningProposal,
)
from aias_awm.llm import StructuredReasoningAdapter
from aias_awm.domain.models import AuditHypothesis
from aias_awm.persistence import Database, HypothesisRepository
from aias_awm.runtime import AuditWorldRuntime


def build_runtime():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    return AuditWorldRuntime(db, LegacyAIASHarnessStub(), source_manifest_hash="SRC1", rule_pack_hash="RULE1")


def requirement():
    return AtomicRequirement(
        requirement_id="AR-6.1.3-E06",
        standard_id="STD-ISO9001-2026",
        clause="6.1.3",
        subject="organization",
        obligation="evaluate",
        object="effectiveness_of_actions_to_address_opportunities",
        semantic_category="D2_SAFE",
        evidence_expectations=[EvidenceExpectation(evidence_type="effectiveness_evaluation", minimum_strength="effectiveness")],
        failure_patterns=["no_acceptance_criteria"],
        negative_inference_rules=["monitoring_data_alone_does_not_prove_effectiveness"],
        version="1.0",
    )


def case():
    return AuditCase(
        audit_case_id="CASE-TII-613",
        organization_id="ORG-TII",
        standard_ids=["STD-ISO9001-2026"],
        audit_type="scenario_assessment",
        scope={"process_ids": ["PROC-CUSTOMER-SERVICE"]},
        created_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )


def evidence(*, breach=False):
    return EvidenceItem(
        evidence_id="EV-BREACH" if breach else "EV-MONITOR",
        organization_id="ORG-TII",
        audit_case_id="CASE-TII-613",
        process_id="PROC-CUSTOMER-SERVICE",
        evidence_type="record",
        assertion="Formal acceptance criteria are absent" if breach else "Pilot monitoring data exists",
        normalized_fact="no formal acceptance criteria" if breach else "performance is monitored",
        epistemic_state=EpistemicState.VERIFIED,
        related_requirement_ids=["AR-6.1.3-E06"],
        metadata={
            "evidence_role": "effectiveness_evaluation" if breach else "monitoring",
            "strength": "effectiveness" if breach else "recorded",
            "polarity": "negative" if breach else "support",
            "proves_breach": breach,
            "proves_effectiveness": False if breach else None,
        },
    )


def test_persistent_runtime_cognitive_cycle_and_graph():
    rt = build_runtime()
    rt.create_case(case())
    rt.register_requirement(requirement())
    rt.ingest_evidence(evidence())
    first = rt.reason("CASE-TII-613", ["AR-6.1.3-E06"])
    assert first["decision_ready"] is False
    assert first["assessments"][0]["state"] == "PARTIALLY_SUPPORTED"
    assert first["actions"][0]["action_type"] == "VERIFY_EFFECTIVENESS"
    assert rt.graph_summary("CASE-TII-613")["nodes"] > 0

    rt.ingest_evidence(evidence(breach=True))
    second = rt.reason("CASE-TII-613", ["AR-6.1.3-E06"])
    assert second["decision_ready"] is True
    assert second["assessments"][0]["state"] == "BREACH_PROVEN"
    snapshot = rt.rebuild_world("ORG-TII")
    assert snapshot.requirement_states[0].breach_proven is True
    assert len(snapshot.hypothesis_states) >= 1


def test_fastapi_contract_end_to_end():
    rt = build_runtime()
    client = TestClient(create_app(rt))
    assert client.get("/health").status_code == 200
    assert client.post("/api/v1/audits/cases", json={"case": case().model_dump(mode="json")}).status_code == 200
    assert client.post("/api/v1/requirements", json={"requirement": requirement().model_dump(mode="json")}).status_code == 200
    assert client.post("/api/v1/audits/CASE-TII-613/evidence", json={"evidence": evidence(breach=True).model_dump(mode="json")}).status_code == 200
    reason = client.post("/api/v1/audits/CASE-TII-613/reason", json={"requirement_ids": ["AR-6.1.3-E06"]})
    assert reason.status_code == 200
    assert reason.json()["decision_ready"] is True
    graph = client.get("/api/v1/audits/CASE-TII-613/graph")
    assert graph.status_code == 200 and graph.json()["nodes"] > 0
    candidate = {
        "gate_execution_trace": {"G0": "PASS", "G1": "PASS"},
        "verdict": "Noncomplied",
        "nc_class": "Minor",
    }
    decision = client.post("/api/v1/audits/CASE-TII-613/decision", json={"candidate": candidate})
    assert decision.status_code == 200
    assert decision.json()["status"] == "HUMAN_REVIEW_REQUIRED"


def test_structured_llm_adapter_rejects_uncontrolled_shape():
    adapter = StructuredReasoningAdapter()
    ok = adapter.safe_parse({"mapped_requirement_ids": ["AR-1"]})
    assert ok["valid"] is True
    bad = adapter.safe_parse({"mapped_requirement_ids": [], "final_certification_decision": "approve"})
    assert bad["valid"] is False


def test_obsolete_planner_action_is_cancelled_after_requirement_resolves():
    rt = build_runtime()
    rt.create_case(case())
    rt.register_requirement(requirement())
    rt.ingest_evidence(evidence())
    rt.reason("CASE-TII-613", ["AR-6.1.3-E06"])
    assert rt.graph_summary("CASE-TII-613")["pending_actions"] == ["ACT-CASE-TII-613-001"]
    rt.ingest_evidence(evidence(breach=True))
    rt.reason("CASE-TII-613", ["AR-6.1.3-E06"])
    summary = rt.graph_summary("CASE-TII-613")
    assert summary["pending_actions"] == []
    assert summary["unresolved_hypotheses"] == []


def test_hypothesis_possible_worlds_dimensions_round_trip_through_sql():
    """references/68-hartley-uncertainty.md wiring: possible_worlds_dimensions
    and known_facts must survive a real insert+select through the
    'hypotheses' SQL table (scripts/awm_runtime/aias_awm/persistence/tables.py),
    not just pass pydantic validation in memory."""
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    repo = HypothesisRepository(db)
    dims = {"AR-6.1.3-E02_record": ["PRESENT", "ABSENT"], "AR-6.1.3-E02_observation": ["YES", "NO"]}
    facts = {"AR-6.1.3-E02_observation": "YES"}
    repo.upsert(AuditHypothesis(
        hypothesis_id="H-ROUNDTRIP", audit_case_id="CASE-RT", hypothesis_type="INSUFFICIENT_EVIDENCE",
        statement="round-trip check", requirement_ids=["AR-6.1.3-E02"], status="UNRESOLVED",
        unresolved_questions=["record:recorded"],
        possible_worlds_dimensions=dims, known_facts=facts,
    ))
    loaded = repo.list_for_case("CASE-RT")
    assert len(loaded) == 1
    assert loaded[0].possible_worlds_dimensions == dims
    assert loaded[0].known_facts == facts


def test_hypothesis_without_dimensions_still_round_trips():
    """The common case today (no clause has been wired to supply dimensions
    yet) must keep working exactly as before this change."""
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    repo = HypothesisRepository(db)
    repo.upsert(AuditHypothesis(
        hypothesis_id="H-PLAIN", audit_case_id="CASE-PLAIN", hypothesis_type="CONFORMITY",
        statement="no dimensions here", requirement_ids=["AR-1"], status="SUPPORTED",
    ))
    loaded = repo.list_for_case("CASE-PLAIN")
    assert loaded[0].possible_worlds_dimensions is None
    assert loaded[0].known_facts == {}
