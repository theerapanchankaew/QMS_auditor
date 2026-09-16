from __future__ import annotations

from datetime import datetime, timezone

from aias_awm.domain.models import AuditAction, AuditHypothesis, RequirementAssessment, WorldEvent


def cognition_events(
    organization_id: str,
    start_sequence: int,
    assessments: list[RequirementAssessment],
    hypotheses: list[AuditHypothesis],
    actions: list[AuditAction],
    *,
    event_time: datetime | None = None,
) -> list[WorldEvent]:
    """Convert cognition outputs into append-only world events."""
    now = event_time or datetime.now(timezone.utc)
    out: list[WorldEvent] = []
    seq = start_sequence
    for a in assessments:
        out.append(WorldEvent(
            event_id=f"EVT-{organization_id}-{seq:08d}", organization_id=organization_id,
            sequence_no=seq, event_type="REQUIREMENT_ASSESSMENT_UPSERTED",
            event_time=now, recorded_at=now, entity_ids=[a.requirement_id],
            payload={"assessment": a.model_dump(mode="json")},
            source_evidence_ids=list(set(a.positive_evidence_ids+a.negative_evidence_ids+a.contradictory_evidence_ids)),
        )); seq += 1
    for h in hypotheses:
        out.append(WorldEvent(
            event_id=f"EVT-{organization_id}-{seq:08d}", organization_id=organization_id,
            sequence_no=seq, event_type="HYPOTHESIS_UPSERTED", event_time=now, recorded_at=now,
            entity_ids=h.requirement_ids, payload={"hypothesis": h.model_dump(mode="json")},
            source_evidence_ids=list(set(h.supporting_evidence_ids+h.contradicting_evidence_ids)),
        )); seq += 1
    for a in actions:
        out.append(WorldEvent(
            event_id=f"EVT-{organization_id}-{seq:08d}", organization_id=organization_id,
            sequence_no=seq, event_type="AUDIT_ACTION_UPSERTED", event_time=now, recorded_at=now,
            entity_ids=a.target_entity_ids+a.target_requirement_ids, payload={"action": a.model_dump(mode="json")},
        )); seq += 1
    return out
