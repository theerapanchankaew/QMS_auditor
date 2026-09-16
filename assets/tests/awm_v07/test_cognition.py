from datetime import datetime, timezone

from aias_awm.cognition import AuditCognitionPipeline
from aias_awm.domain.models import AtomicRequirement, EvidenceExpectation, EvidenceItem, EpistemicState
from aias_awm.graph import AuditGraphProjector

UTC = timezone.utc


def _req():
    return AtomicRequirement(
        requirement_id="AR-6.1.3-E06", standard_id="STD-ISO9001-2026", clause="6.1.3",
        subject="organization", obligation="evaluate", object="effectiveness_of_actions_to_address_opportunities",
        semantic_category="D2_SAFE",
        evidence_expectations=[EvidenceExpectation(evidence_type="effectiveness_evaluation", minimum_strength="effectiveness", mandatory=True)],
        failure_patterns=["no_acceptance_criteria"], negative_inference_rules=["monitoring_alone_not_effectiveness"], version="1.0",
    )


def test_missing_effectiveness_evidence_does_not_create_breach():
    ev = EvidenceItem(
        evidence_id="EV-1", organization_id="ORG-TII", audit_case_id="CASE-1", evidence_type="measurement",
        assertion="Pilot metrics are available", epistemic_state=EpistemicState.VERIFIED,
        related_requirement_ids=["AR-6.1.3-E06"], metadata={"evidence_role": "performance_data", "strength": "verified"},
    )
    result = AuditCognitionPipeline().run(audit_case_id="CASE-1", atomic_requirements=[_req()], evidence_items=[ev], now=datetime(2026,9,11,tzinfo=UTC))
    a = result.assessments[0]
    assert a.breach_proven is False
    assert a.state.value == "PARTIALLY_SUPPORTED"
    assert result.decision_ready is False
    assert result.actions[0].action_type == "VERIFY_EFFECTIVENESS"


def test_explicit_breach_evidence_can_resolve_requirement():
    ev = EvidenceItem(
        evidence_id="EV-2", organization_id="ORG-TII", audit_case_id="CASE-1", evidence_type="record",
        assertion="Management confirms there is no formal acceptance criterion and no effectiveness evaluation record.",
        epistemic_state=EpistemicState.VERIFIED, related_requirement_ids=["AR-6.1.3-E06"],
        metadata={"polarity": "negative", "proves_breach": True, "proves_effectiveness": False, "strength": "effectiveness", "evidence_role": "effectiveness_evaluation"},
    )
    result = AuditCognitionPipeline().run(audit_case_id="CASE-1", atomic_requirements=[_req()], evidence_items=[ev], now=datetime(2026,9,11,tzinfo=UTC))
    a = result.assessments[0]
    assert a.state.value == "BREACH_PROVEN"
    assert a.breach_proven is True
    assert a.effectiveness_proven is False
    assert result.decision_ready is True


def test_graph_projection_links_evidence_assessment_hypothesis_action():
    ev = EvidenceItem(
        evidence_id="EV-1", organization_id="ORG", audit_case_id="CASE", evidence_type="measurement",
        assertion="metrics", epistemic_state=EpistemicState.VERIFIED, related_requirement_ids=["AR-6.1.3-E06"],
        metadata={"evidence_role": "performance_data", "strength": "verified"},
    )
    result = AuditCognitionPipeline().run(audit_case_id="CASE", atomic_requirements=[_req()], evidence_items=[ev])
    graph = AuditGraphProjector().project([_req()], [ev], list(result.assessments), list(result.hypotheses), list(result.actions))
    relations = {r for _, r, _, _ in graph.edges}
    assert "ASSESSES" in relations
    assert "SEEKS_EVIDENCE_FOR" in relations
    assert "CONCERNS" in relations
