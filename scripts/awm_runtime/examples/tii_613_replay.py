from datetime import datetime, timezone

from aias_awm.adapters import LegacyAIASHarnessStub
from aias_awm.control import WorldFSM, WorldGateEngine, WorldState, WorldToDecisionAdapter
from aias_awm.domain.models import EntityState, RequirementAssessment, RequirementState, WorldEvent
from aias_awm.world import InMemoryEventStore, WorldReducer, WorldRepository


UTC = timezone.utc
ORG = "ORG-TII"
CASE = "CASE-TII-613-001"
REQ = "AR-6.1.3-E06"


def main() -> None:
    store = InMemoryEventStore()
    reducer = WorldReducer(source_manifest_hash="SRC-MANIFEST-DEMO", rule_pack_hash="RULEPACK-DEMO")
    repo = WorldRepository(store, reducer)
    fsm = WorldFSM()
    fsm.transition(WorldState.W1_WORLD_LOADED)

    process = EntityState(
        entity_id="PROC-CUSTOMER-SERVICE",
        entity_type="process",
        attributes={"name": "Customer Service", "ai_chatbot_pilot": True},
        effective_from=datetime(2026, 8, 1, tzinfo=UTC),
    )
    repo.append_and_load(WorldEvent(
        event_id="EVT-000",
        organization_id=ORG,
        sequence_no=0,
        event_type="PROCESS_UPSERTED",
        event_time=datetime(2026, 8, 1, tzinfo=UTC),
        recorded_at=datetime(2026, 8, 1, tzinfo=UTC),
        entity_ids=[process.entity_id],
        payload={"entity": process.model_dump(mode="json")},
    ))
    fsm.transition(WorldState.W2_OBSERVATION_INGESTED)
    fsm.transition(WorldState.W3_WORLD_UPDATED)
    fsm.transition(WorldState.W4_UNCERTAINTY_ANALYZED)
    fsm.transition(WorldState.W5_HYPOTHESES_UPDATED)
    fsm.transition(WorldState.W8_WORLD_RECONCILED)

    assessment = RequirementAssessment(
        assessment_id="RA-TII-613-E06",
        audit_case_id=CASE,
        requirement_id=REQ,
        applicability="APPLICABLE",
        state=RequirementState.BREACH_PROVEN,
        positive_evidence_ids=["EV-PILOT-MONITORING"],
        negative_evidence_ids=["EV-NO-FORMAL-ACCEPTANCE-CRITERIA"],
        missing_evidence=[],
        coverage_ratio=1.0,
        breach_proven=True,
        effectiveness_proven=False,
        reasoning_candidate="Actions were implemented and monitored, but formal effectiveness evaluation criteria were not demonstrated.",
        updated_at=datetime(2026, 9, 11, tzinfo=UTC),
    )
    snapshot = repo.append_and_load(WorldEvent(
        event_id="EVT-001",
        organization_id=ORG,
        sequence_no=1,
        event_type="REQUIREMENT_ASSESSMENT_UPSERTED",
        event_time=datetime(2026, 9, 11, tzinfo=UTC),
        recorded_at=datetime(2026, 9, 11, tzinfo=UTC),
        entity_ids=[REQ],
        payload={"assessment": assessment.model_dump(mode="json")},
    ))
    fsm.transition(WorldState.W9_AUDIT_READY)

    candidate = {
        "verdict": "Noncomplied",
        "nc_class": "Minor",
        "clause": "6.1.3",
        "gate_execution_trace": {"G5": "BREACH_PROVEN", "G8": "NO_MAJOR_TRIGGER"},
    }
    adapter = WorldToDecisionAdapter(WorldGateEngine(), LegacyAIASHarnessStub())
    result = adapter.decide(snapshot, candidate, context={"audit_case_id": CASE})

    print("World state:", fsm.state.value)
    print("Snapshot:", snapshot.snapshot_id)
    print("Decision status:", result["status"])


if __name__ == "__main__":
    main()
