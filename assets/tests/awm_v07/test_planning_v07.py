from datetime import datetime, timezone

from fastapi.testclient import TestClient

from aias_awm.adapters.legacy_harness import LegacyAIASHarnessStub
from aias_awm.api import create_app
from aias_awm.domain.models import AuditAction, AuditCase, AuditHypothesis
from aias_awm.persistence import Database
from aias_awm.planning import (
    AutonomousAuditPlanningPolicy,
    PlanningContext,
    TemporalSamplingPlanner,
    evaluate_next_action,
    next_action_agreement,
    mean_reciprocal_rank,
)
from aias_awm.runtime import AuditWorldRuntime

NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)


def test_information_gain_ranking_prioritizes_effectiveness():
    h = AuditHypothesis(
        hypothesis_id="H1", audit_case_id="C1", hypothesis_type="INSUFFICIENT_EVIDENCE",
        statement="effectiveness unresolved", requirement_ids=["AR1"], status="UNRESOLVED",
        unresolved_questions=["effectiveness evaluation record", "approval record"],
    )
    ctx = PlanningContext(
        audit_case_id="C1", unresolved_requirement_ids=["AR1"], unresolved_hypothesis_ids=["H1"],
        created_at=NOW,
    )
    d = AutonomousAuditPlanningPolicy().plan(context=ctx, hypotheses=[h])
    assert d.stop_decision == "CONTINUE"
    assert d.ranked_actions[0].action.action_type == "VERIFY_EFFECTIVENESS"
    assert d.selected_action_id == d.ranked_actions[0].action.action_id


def test_information_gain_uses_real_hartley_measure_when_dimensions_present():
    """references/68-hartley-uncertainty.md wiring: a hypothesis carrying
    possible_worlds_dimensions (as loaded from a clause's
    assets/requirement_profiles/<clause>.json corpus entry) gets an exact
    log2(k)-bit info_gain instead of the hand-picked 0.80/0.95 constant used
    by test_information_gain_ranking_prioritizes_effectiveness above (which
    has no dimensions and must keep using the old heuristic unchanged)."""
    h = AuditHypothesis(
        hypothesis_id="H1", audit_case_id="C1", hypothesis_type="INSUFFICIENT_EVIDENCE",
        statement="objective record unresolved", requirement_ids=["AR-6.1.3-E02"], status="UNRESOLVED",
        unresolved_questions=["record:recorded"],
        possible_worlds_dimensions={
            "AR-6.1.3-E02_implementation": ["YES", "NO"],
            "AR-6.1.3-E02_effectiveness_evaluated": ["YES", "NO"],
            "AR-6.1.3-E02_record": ["PRESENT", "ABSENT"],
        },
    )
    ctx = PlanningContext(
        audit_case_id="C1", unresolved_requirement_ids=["AR-6.1.3-E02"], unresolved_hypothesis_ids=["H1"],
        created_at=NOW,
    )
    d = AutonomousAuditPlanningPolicy().plan(context=ctx, hypotheses=[h])
    action = d.ranked_actions[0].action
    assert action.action_type == "REQUEST_RECORD"
    # H(Xt)=log2(8)=3 bits; resolving 'record' (k=2 surviving values) -> log2(2)=1 bit -> normalized 1/3
    assert abs(action.expected_information_gain - (1.0 / 3.0)) < 1e-6, action.expected_information_gain


def test_contradiction_forces_cross_check_candidate():
    h = AuditHypothesis(
        hypothesis_id="H1", audit_case_id="C1", hypothesis_type="BREACH", statement="conflict",
        requirement_ids=["AR1"], status="SUPPORTED", unresolved_questions=["record evidence"],
    )
    ctx = PlanningContext(
        audit_case_id="C1", unresolved_requirement_ids=["AR1"], unresolved_hypothesis_ids=["H1"],
        contradictory_evidence_ids=["EV-A", "EV-B"], created_at=NOW,
    )
    d = AutonomousAuditPlanningPolicy().plan(context=ctx, hypotheses=[h])
    assert any(x.action.action_type == "CROSS_CHECK" for x in d.ranked_actions)


def test_budget_blocks_actions_and_escalates_critical_unknown():
    h = AuditHypothesis(
        hypothesis_id="H1", audit_case_id="C1", hypothesis_type="INSUFFICIENT_EVIDENCE",
        statement="unknown", requirement_ids=["AR1"], status="UNRESOLVED",
        unresolved_questions=["effectiveness evidence"],
    )
    ctx = PlanningContext(
        audit_case_id="C1", unresolved_requirement_ids=["AR1"], unresolved_hypothesis_ids=["H1"],
        critical_unknowns=["effectiveness"], max_action_cost=0.10, created_at=NOW,
    )
    d = AutonomousAuditPlanningPolicy().plan(context=ctx, hypotheses=[h])
    assert d.stop_decision == "ESCALATE_HUMAN"
    assert d.selected_action_id is None
    assert all(not x.score.admissible for x in d.ranked_actions)


def test_stop_when_decision_ready():
    ctx = PlanningContext(audit_case_id="C1", decision_ready=True, created_at=NOW)
    d = AutonomousAuditPlanningPolicy().plan(context=ctx, hypotheses=[])
    assert d.stop_decision == "STOP_DECISION_READY"
    assert d.selected_action_id is None


def test_temporal_sampling_expands_for_recurrence():
    p = TemporalSamplingPlanner().plan(
        case_id="C1", population_size=100, current_sample_size=5,
        recurrence_signal=True, stale_periods=["2025-Q4"],
    )
    assert p.strategy == "RECURRENCE_TARGETED"
    assert p.additional_sample_size > 5


def test_next_action_metrics():
    e1 = evaluate_next_action("C1", ["REQUEST_RECORD", "VERIFY_EFFECTIVENESS"], ["VERIFY_EFFECTIVENESS"])
    e2 = evaluate_next_action("C2", ["CROSS_CHECK"], ["CROSS_CHECK", "TRACE_TRANSACTION"])
    assert e1.matched and e1.reciprocal_rank == 0.5
    assert next_action_agreement([e1, e2]) == 1.0
    assert mean_reciprocal_rank([e1, e2]) == 0.75


def test_planning_api_persists_decision():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    rt = AuditWorldRuntime(db, LegacyAIASHarnessStub())
    case = AuditCase(
        audit_case_id="C-API", organization_id="ORG", standard_ids=["ISO9001"],
        audit_type="document_review", scope={}, created_at=NOW,
    )
    rt.create_case(case)
    # no assessments yet => not decision ready; critical unknown with no actions => escalate
    client = TestClient(create_app(rt))
    r = client.post("/api/v1/audits/C-API/plan", json={"critical_unknowns": ["scope evidence"]})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"]["stop_decision"] == "ESCALATE_HUMAN"
    latest = rt.planning_runs.latest_for_case("C-API")
    assert latest is not None


def test_sampling_api():
    db = Database("sqlite+pysqlite:///:memory:")
    db.create_schema()
    rt = AuditWorldRuntime(db, LegacyAIASHarnessStub())
    rt.create_case(AuditCase(
        audit_case_id="C-S", organization_id="ORG-S", standard_ids=["ISO9001"],
        audit_type="record_sampling", scope={}, created_at=NOW,
    ))
    client = TestClient(create_app(rt))
    r = client.post("/api/v1/audits/C-S/sampling/plan", json={
        "population_size": 100, "current_sample_size": 5, "high_risk": True,
        "recurrence_signal": False, "stale_periods": []
    })
    assert r.status_code == 200
    assert r.json()["additional_sample_size"] > 0
