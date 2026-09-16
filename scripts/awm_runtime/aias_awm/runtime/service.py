from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aias_awm.cognition.events import cognition_events
from aias_awm.cognition.pipeline import AuditCognitionPipeline
from aias_awm.control.decision_adapter import WorldToDecisionAdapter
from aias_awm.control.world_gates import WorldGateEngine
from aias_awm.domain.models import AuditCase, AtomicRequirement, EvidenceItem, WorldEvent, WorldSnapshot
from aias_awm.graph import AuditWorldGraph
from aias_awm.persistence import (
    AuditActionRepository,
    AuditCaseRepository,
    AtomicRequirementRepository,
    EvidenceRepository,
    HypothesisRepository,
    RequirementAssessmentRepository,
    WorldEventRepository,
)
from aias_awm.world.reducer import WorldReducer
from aias_awm.planning import AutonomousAuditPlanningPolicy, PlanningContext
from aias_awm.persistence import PlanningDecisionRepository


class AuditWorldRuntime:
    """Persistent cognitive runtime.

    PostgreSQL/SQLAlchemy repositories are authoritative for cognitive artifacts.
    World state is reconstructed from the append-only event stream. The graph is a
    derived projection. LLMs may propose; deterministic gates/harness control release.
    """

    def __init__(self, db, harness, *, source_manifest_hash: str="DEV-SOURCE", rule_pack_hash: str="DEV-RULES") -> None:
        self.db = db
        self.cases = AuditCaseRepository(db)
        self.requirements = AtomicRequirementRepository(db)
        self.evidence = EvidenceRepository(db)
        self.assessments = RequirementAssessmentRepository(db)
        self.hypotheses = HypothesisRepository(db)
        self.actions = AuditActionRepository(db)
        self.events = WorldEventRepository(db)
        self.reducer = WorldReducer(source_manifest_hash, rule_pack_hash)
        self.cognition = AuditCognitionPipeline()
        self.graph = AuditWorldGraph()
        self.decision = WorldToDecisionAdapter(WorldGateEngine(), harness)
        self.planner = AutonomousAuditPlanningPolicy()
        self.planning_runs = PlanningDecisionRepository(db)

    def create_case(self, case: AuditCase) -> AuditCase:
        self.cases.upsert(case)
        if self.events.last_sequence(case.organization_id) < 0:
            now = case.created_at
            self.events.append(WorldEvent(
                event_id=f"EVT-{case.organization_id}-00000000",
                organization_id=case.organization_id,
                sequence_no=0,
                event_type="AUDIT_CASE_CREATED",
                event_time=now,
                recorded_at=now,
                entity_ids=[case.audit_case_id],
                payload={"audit_case_id": case.audit_case_id},
            ))
        return case

    def register_requirement(self, requirement: AtomicRequirement) -> None:
        self.requirements.upsert(requirement)

    def ingest_evidence(self, item: EvidenceItem) -> WorldSnapshot:
        case = self._require_case(item.audit_case_id)
        self.evidence.upsert(item)
        seq = self.events.last_sequence(case.organization_id) + 1
        now = item.observed_at or datetime.now(timezone.utc)
        self.events.append(WorldEvent(
            event_id=f"EVT-{case.organization_id}-{seq:08d}",
            organization_id=case.organization_id,
            sequence_no=seq,
            event_type="EVIDENCE_INGESTED",
            event_time=now,
            recorded_at=datetime.now(timezone.utc),
            entity_ids=item.related_requirement_ids,
            source_evidence_ids=[item.evidence_id],
            payload={"evidence_id": item.evidence_id},
        ))
        return self.rebuild_world(case.organization_id)

    def reason(self, case_id: str, requirement_ids: list[str]) -> dict[str, Any]:
        case = self._require_case(case_id)
        requirements = self.requirements.get_many(requirement_ids)
        missing = sorted(set(requirement_ids) - {r.requirement_id for r in requirements})
        if missing:
            raise KeyError(f"unknown requirements: {missing}")
        evidence = self.evidence.list_for_case(case_id)
        result = self.cognition.run(
            audit_case_id=case_id,
            atomic_requirements=requirements,
            evidence_items=evidence,
            now=datetime.now(timezone.utc),
        )
        for item in result.assessments: self.assessments.upsert(item)
        for item in result.hypotheses: self.hypotheses.upsert(item)
        active_ids = {item.action_id for item in result.actions}
        cancelled = self.actions.cancel_obsolete(case_id, active_ids)
        for item in result.actions: self.actions.upsert(item)

        start = self.events.last_sequence(case.organization_id) + 1
        emitted = cognition_events(
            case.organization_id, start,
            list(result.assessments), list(result.hypotheses), list(cancelled) + list(result.actions),
        )
        for event in emitted: self.events.append(event)
        snapshot = self.rebuild_world(case.organization_id)
        case.world_snapshot_id = snapshot.snapshot_id
        self.cases.upsert(case)

        self.graph.rebuild(evidence, list(result.assessments), list(result.hypotheses), list(result.actions))
        return {
            "audit_case_id": case_id,
            "world_snapshot_id": snapshot.snapshot_id,
            "decision_ready": result.decision_ready,
            "assessments": [x.model_dump(mode="json") for x in result.assessments],
            "hypotheses": [x.model_dump(mode="json") for x in result.hypotheses],
            "actions": [x.model_dump(mode="json") for x in result.actions],
            "events_emitted": [x.event_id for x in emitted],
        }


    def plan_next_actions(
        self, case_id: str, *, remaining_time_minutes: float | None = None,
        max_action_cost: float | None = None, critical_unknowns: list[str] | None = None
    ) -> dict[str, Any]:
        case = self._require_case(case_id)
        assessments = self.assessments.list_for_case(case_id)
        hypotheses = self.hypotheses.list_for_case(case_id)
        evidence = self.evidence.list_for_case(case_id)
        unresolved = [a.requirement_id for a in assessments if a.state.value not in {"SATISFIED", "BREACH_PROVEN", "NOT_APPLICABLE"}]
        contradictions = sorted({eid for a in assessments for eid in a.contradictory_evidence_ids})
        stale = sorted({e.evidence_id for e in evidence if getattr(e.epistemic_state, "value", str(e.epistemic_state)) == "STALE"})
        decision_ready = bool(assessments) and all(a.state.value in {"SATISFIED", "BREACH_PROVEN", "NOT_APPLICABLE"} for a in assessments) and not contradictions
        ctx = PlanningContext(
            audit_case_id=case_id,
            unresolved_requirement_ids=unresolved,
            unresolved_hypothesis_ids=[h.hypothesis_id for h in hypotheses if h.status in {"UNRESOLVED", "SUPPORTED"}],
            contradictory_evidence_ids=contradictions,
            stale_evidence_ids=stale,
            remaining_time_minutes=remaining_time_minutes,
            max_action_cost=max_action_cost,
            decision_ready=decision_ready,
            critical_unknowns=critical_unknowns or [],
            created_at=datetime.now(timezone.utc),
        )
        result = self.planner.plan(context=ctx, hypotheses=hypotheses)
        run_id = f"PLAN-{case_id}-{int(result.created_at.timestamp()*1000000)}"
        self.planning_runs.save(run_id, ctx, result)
        return {
            "planning_run_id": run_id,
            "context": ctx.model_dump(mode="json"),
            "decision": result.model_dump(mode="json"),
        }

    def list_actions(self, case_id: str):
        self._require_case(case_id)
        return self.actions.list_for_case(case_id)

    def make_decision(self, case_id: str, candidate: dict[str, Any], context: dict[str, Any] | None=None) -> dict[str, Any]:
        case = self._require_case(case_id)
        snapshot = self.rebuild_world(case.organization_id)
        enriched = dict(context or {})
        enriched["audit_case_id"] = case_id
        return self.decision.decide(snapshot, candidate, enriched)

    def rebuild_world(self, organization_id: str) -> WorldSnapshot:
        return self.reducer.replay(organization_id, self.events.list(organization_id))

    def graph_summary(self, case_id: str) -> dict[str, Any]:
        self._require_case(case_id)
        evidence = self.evidence.list_for_case(case_id)
        assessments = self.assessments.list_for_case(case_id)
        hypotheses = self.hypotheses.list_for_case(case_id)
        actions = self.actions.list_for_case(case_id)
        self.graph.rebuild(evidence, assessments, hypotheses, actions)
        return {
            "nodes": self.graph.graph.number_of_nodes(),
            "edges": self.graph.graph.number_of_edges(),
            "unresolved_hypotheses": self.graph.unresolved_hypotheses(),
            "pending_actions": self.graph.pending_actions(),
        }

    def _require_case(self, case_id: str | None) -> AuditCase:
        if not case_id:
            raise KeyError("audit_case_id is required")
        case = self.cases.get(case_id)
        if case is None:
            raise KeyError(f"unknown audit case: {case_id}")
        return case
