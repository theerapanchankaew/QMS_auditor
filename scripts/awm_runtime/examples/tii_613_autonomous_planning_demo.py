from datetime import datetime, timezone

from aias_awm.domain.models import AuditHypothesis
from aias_awm.planning import AutonomousAuditPlanningPolicy, PlanningContext

now = datetime.now(timezone.utc)
hypotheses = [
    AuditHypothesis(
        hypothesis_id="HYP-TII-613-EFF",
        audit_case_id="CASE-TII-613",
        hypothesis_type="INSUFFICIENT_EVIDENCE",
        statement="Effectiveness evaluation remains unresolved",
        requirement_ids=["AR-6.1.3-E06"],
        status="UNRESOLVED",
        unresolved_questions=[
            "formal effectiveness evaluation record",
            "approved acceptance criteria",
        ],
    )
]
ctx = PlanningContext(
    audit_case_id="CASE-TII-613",
    unresolved_requirement_ids=["AR-6.1.3-E06"],
    unresolved_hypothesis_ids=["HYP-TII-613-EFF"],
    contradictory_evidence_ids=[],
    stale_evidence_ids=[],
    remaining_time_minutes=90,
    max_action_cost=1.0,
    decision_ready=False,
    critical_unknowns=["effectiveness criteria"],
    created_at=now,
)
result = AutonomousAuditPlanningPolicy().plan(context=ctx, hypotheses=hypotheses)
print(result.model_dump_json(indent=2))
