from datetime import datetime, timezone

import pytest

from aias_awm.control import WorldFSM, WorldGateEngine, WorldState
from aias_awm.domain.models import EntityState, RequirementAssessment, RequirementState, WorldEvent
from aias_awm.world import InMemoryEventStore, WorldReducer, WorldRepository, sha256_obj

UTC = timezone.utc


def test_world_replay_is_deterministic():
    store = InMemoryEventStore()
    reducer = WorldReducer("src", "rules")
    repo = WorldRepository(store, reducer)
    entity = EntityState(entity_id="P1", entity_type="process", attributes={"x": 1}, effective_from=datetime(2026,1,1,tzinfo=UTC))
    event = WorldEvent(event_id="E0", organization_id="ORG", sequence_no=0, event_type="PROCESS_UPSERTED", event_time=datetime(2026,1,1,tzinfo=UTC), recorded_at=datetime(2026,1,1,tzinfo=UTC), payload={"entity": entity.model_dump(mode="json")})
    repo.append_and_load(event)
    a = repo.load("ORG")
    b = reducer.replay("ORG", store.list("ORG"))
    assert a.snapshot_id == b.snapshot_id
    assert sha256_obj(a.model_dump(mode="json")) == sha256_obj(b.model_dump(mode="json"))


def test_event_sequence_is_enforced():
    store = InMemoryEventStore()
    with pytest.raises(ValueError):
        store.append(WorldEvent(event_id="E2", organization_id="ORG", sequence_no=2, event_type="NOOP", event_time=datetime.now(UTC), recorded_at=datetime.now(UTC)))


def test_world_fsm_blocks_shortcuts():
    fsm = WorldFSM()
    with pytest.raises(ValueError):
        fsm.transition(WorldState.W9_AUDIT_READY)


def test_wg6_passes_only_resolved_material_requirement():
    reducer = WorldReducer("src", "rules")
    snap = reducer.empty_snapshot("ORG")
    gates = WorldGateEngine().evaluate(snap)
    assert next(g for g in gates if g.gate_id == "WG6").result == "BLOCK"

    ra = RequirementAssessment(
        assessment_id="RA1", audit_case_id="C1", requirement_id="AR1",
        applicability="APPLICABLE", state=RequirementState.BREACH_PROVEN,
        breach_proven=True, updated_at=datetime.now(UTC)
    )
    data = snap.model_dump(mode="python")
    data["requirement_states"] = [ra.model_dump(mode="python")]
    snap2 = type(snap).model_validate(data)
    gates2 = WorldGateEngine().evaluate(snap2)
    assert next(g for g in gates2 if g.gate_id == "WG6").result == "PASS"
