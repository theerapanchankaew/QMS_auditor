from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Iterable

from aias_awm.domain.models import EntityState, RequirementAssessment, AuditHypothesis, AuditAction, WorldEvent, WorldSnapshot
from aias_awm.world.hashing import sha256_obj


ENTITY_EVENT_MAP = {
    "PROCESS_UPSERTED": "process_states",
    "CONTROL_UPSERTED": "control_states",
    "RISK_UPSERTED": "risk_states",
    "OPPORTUNITY_UPSERTED": "opportunity_states",
}


class WorldReducer:
    def __init__(self, source_manifest_hash: str, rule_pack_hash: str) -> None:
        self.source_manifest_hash = source_manifest_hash
        self.rule_pack_hash = rule_pack_hash

    def empty_snapshot(self, organization_id: str) -> WorldSnapshot:
        return WorldSnapshot(
            snapshot_id=f"WS-{organization_id}-INIT",
            organization_id=organization_id,
            as_of=datetime(1970, 1, 1, tzinfo=timezone.utc),
            process_states=[],
            control_states=[],
            risk_states=[],
            opportunity_states=[],
            requirement_states=[],
            hypothesis_states=[],
            action_states=[],
            source_manifest_hash=self.source_manifest_hash,
            rule_pack_hash=self.rule_pack_hash,
            created_from_event_seq=0,
        )

    def apply(self, snapshot: WorldSnapshot, event: WorldEvent) -> WorldSnapshot:
        if snapshot.organization_id != event.organization_id:
            raise ValueError("event organization does not match snapshot")

        data = snapshot.model_dump(mode="python")

        if event.event_type in ENTITY_EVENT_MAP:
            collection_name = ENTITY_EVENT_MAP[event.event_type]
            entity_payload = event.payload.get("entity")
            if not entity_payload:
                raise ValueError(f"{event.event_type} requires payload.entity")
            entity = EntityState.model_validate(entity_payload)
            collection = [EntityState.model_validate(x) for x in data[collection_name]]
            collection = [x for x in collection if x.entity_id != entity.entity_id]
            collection.append(entity)
            data[collection_name] = [x.model_dump(mode="python") for x in collection]

        elif event.event_type == "REQUIREMENT_ASSESSMENT_UPSERTED":
            payload = event.payload.get("assessment")
            if not payload:
                raise ValueError("REQUIREMENT_ASSESSMENT_UPSERTED requires payload.assessment")
            assessment = RequirementAssessment.model_validate(payload)
            collection = [RequirementAssessment.model_validate(x) for x in data["requirement_states"]]
            collection = [x for x in collection if x.assessment_id != assessment.assessment_id]
            collection.append(assessment)
            data["requirement_states"] = [x.model_dump(mode="python") for x in collection]

        elif event.event_type == "HYPOTHESIS_UPSERTED":
            payload = event.payload.get("hypothesis")
            if not payload:
                raise ValueError("HYPOTHESIS_UPSERTED requires payload.hypothesis")
            hypothesis = AuditHypothesis.model_validate(payload)
            collection = [AuditHypothesis.model_validate(x) for x in data["hypothesis_states"]]
            collection = [x for x in collection if x.hypothesis_id != hypothesis.hypothesis_id]
            collection.append(hypothesis)
            data["hypothesis_states"] = [x.model_dump(mode="python") for x in collection]

        elif event.event_type == "AUDIT_ACTION_UPSERTED":
            payload = event.payload.get("action")
            if not payload:
                raise ValueError("AUDIT_ACTION_UPSERTED requires payload.action")
            action = AuditAction.model_validate(payload)
            collection = [AuditAction.model_validate(x) for x in data["action_states"]]
            collection = [x for x in collection if x.action_id != action.action_id]
            collection.append(action)
            data["action_states"] = [x.model_dump(mode="python") for x in collection]

        elif event.event_type in {"NOOP", "EVIDENCE_INGESTED", "AUDIT_CASE_CREATED"}:
            pass
        else:
            raise ValueError(f"unsupported event_type: {event.event_type}")

        snapshot_time = snapshot.as_of if snapshot.as_of.tzinfo is not None else snapshot.as_of.replace(tzinfo=timezone.utc)
        event_time = event.event_time if event.event_time.tzinfo is not None else event.event_time.replace(tzinfo=timezone.utc)
        data["as_of"] = max(snapshot_time, event_time)
        data["created_from_event_seq"] = event.sequence_no
        data["snapshot_id"] = "PENDING"
        provisional = WorldSnapshot.model_validate(data)
        digest = sha256_obj(provisional.model_dump(mode="json", exclude={"snapshot_id"}))
        data["snapshot_id"] = f"WS-{event.organization_id}-{event.sequence_no}-{digest[:12]}"
        return WorldSnapshot.model_validate(data)

    def replay(self, organization_id: str, events: Iterable[WorldEvent]) -> WorldSnapshot:
        snapshot = self.empty_snapshot(organization_id)
        for event in sorted(events, key=lambda e: e.sequence_no):
            snapshot = self.apply(snapshot, event)
        return snapshot
