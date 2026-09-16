from datetime import datetime, timezone
import json

from aias_awm.cognition import AuditCognitionPipeline
from aias_awm.domain.models import AtomicRequirement, EvidenceExpectation, EvidenceItem, EpistemicState
from aias_awm.graph import AuditGraphProjector

UTC = timezone.utc
CASE = "CASE-TII-613-001"
REQ_ID = "AR-6.1.3-E06"

req = AtomicRequirement(
    requirement_id=REQ_ID,
    standard_id="STD-ISO9001-2026",
    clause="6.1.3",
    subject="organization",
    obligation="evaluate",
    object="effectiveness_of_actions_to_address_opportunities",
    semantic_category="D2_SAFE",
    evidence_expectations=[EvidenceExpectation(
        evidence_type="effectiveness_evaluation",
        minimum_strength="effectiveness",
        mandatory=True,
    )],
    failure_patterns=["no_acceptance_criteria", "results_without_effectiveness_evaluation"],
    negative_inference_rules=["monitoring_data_alone_does_not_prove_effectiveness"],
    version="1.0",
)

pilot_metrics = EvidenceItem(
    evidence_id="EV-TII-001",
    organization_id="ORG-TII",
    audit_case_id=CASE,
    process_id="PROC-CUSTOMER-SERVICE",
    evidence_type="measurement",
    assertion="Pilot has response time, self-service and error measurements.",
    normalized_fact="Performance monitoring data exists.",
    epistemic_state=EpistemicState.VERIFIED,
    observed_at=datetime(2026, 8, 31, tzinfo=UTC),
    related_requirement_ids=[REQ_ID],
    metadata={"evidence_role": "performance_data", "strength": "verified"},
)

pipeline = AuditCognitionPipeline()
step1 = pipeline.run(audit_case_id=CASE, atomic_requirements=[req], evidence_items=[pilot_metrics])
print("STEP 1 - BEFORE DECISION-CRITICAL EVIDENCE")
print(json.dumps({
    "assessment": step1.assessments[0].model_dump(mode="json"),
    "hypothesis": step1.hypotheses[0].model_dump(mode="json"),
    "next_action": step1.actions[0].model_dump(mode="json"),
    "decision_ready": step1.decision_ready,
}, ensure_ascii=False, indent=2))

verified_gap = EvidenceItem(
    evidence_id="EV-TII-002",
    organization_id="ORG-TII",
    audit_case_id=CASE,
    process_id="PROC-CUSTOMER-SERVICE",
    evidence_type="record",
    assertion="Verified project record states that formal pilot acceptance criteria/effectiveness evaluation were not established.",
    normalized_fact="Required effectiveness evaluation is absent and this absence is directly verified.",
    epistemic_state=EpistemicState.VERIFIED,
    related_requirement_ids=[REQ_ID],
    metadata={
        "polarity": "negative",
        "proves_breach": True,
        "proves_effectiveness": False,
        "evidence_role": "effectiveness_evaluation",
        "strength": "effectiveness",
    },
)

step2 = pipeline.run(audit_case_id=CASE, atomic_requirements=[req], evidence_items=[pilot_metrics, verified_gap])
print("\nSTEP 2 - AFTER VERIFIED BREACH EVIDENCE")
print(json.dumps({
    "assessment": step2.assessments[0].model_dump(mode="json"),
    "hypothesis": step2.hypotheses[0].model_dump(mode="json"),
    "actions": [x.model_dump(mode="json") for x in step2.actions],
    "decision_ready": step2.decision_ready,
}, ensure_ascii=False, indent=2))

graph = AuditGraphProjector().project([req], [pilot_metrics, verified_gap], list(step2.assessments), list(step2.hypotheses), list(step2.actions))
print("\nGRAPH SUMMARY")
print(json.dumps({"nodes": len(graph.nodes), "edges": len(graph.edges), "relations": sorted({x[1] for x in graph.edges})}, indent=2))
