from __future__ import annotations

from fastapi import FastAPI, HTTPException

from aias_awm.api.contracts import CreateCaseRequest, DecisionRequest, IngestEvidenceRequest, ReasonRequest, RegisterRequirementRequest, RecordTemporalFactRequest, AsOfWorldRequest, RecurrenceRequest, PlanNextActionsRequest, SamplingPlanRequest
from aias_awm.runtime import AuditWorldRuntime
from aias_awm.perception.runtime import PersistentPerceptionRuntime
from aias_awm.api.perception_contracts import IngestSourceRequest, RetrievalRequest
from aias_awm.planning import TemporalSamplingPlanner


def create_app(runtime: AuditWorldRuntime) -> FastAPI:
    app = FastAPI(title="AIAS Audit World Model API", version="0.7.0")
    perception = PersistentPerceptionRuntime(runtime.db)
    from aias_awm.temporal import TemporalAuditRuntime
    temporal = TemporalAuditRuntime(runtime.db)
    sampling_planner = TemporalSamplingPlanner()

    def call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/health")
    def health():
        return {"status": "ok", "architecture": "AIAS-AWM", "version": "0.7.0"}

    @app.post("/api/v1/audits/cases")
    def create_case(req: CreateCaseRequest):
        case = call(runtime.create_case, req.case)
        snapshot = runtime.rebuild_world(case.organization_id)
        return {"case": case.model_dump(mode="json"), "world_snapshot_id": snapshot.snapshot_id}

    @app.post("/api/v1/requirements")
    def register_requirement(req: RegisterRequirementRequest):
        call(runtime.register_requirement, req.requirement)
        return {"status": "registered", "requirement_id": req.requirement.requirement_id}

    @app.post("/api/v1/audits/{case_id}/evidence")
    def ingest_evidence(case_id: str, req: IngestEvidenceRequest):
        if req.evidence.audit_case_id != case_id:
            raise HTTPException(status_code=422, detail="path case_id and evidence.audit_case_id differ")
        snapshot = call(runtime.ingest_evidence, req.evidence)
        return {"evidence_id": req.evidence.evidence_id, "world_snapshot_id": snapshot.snapshot_id}

    @app.post("/api/v1/audits/{case_id}/reason")
    def reason(case_id: str, req: ReasonRequest):
        return call(runtime.reason, case_id, req.requirement_ids)

    @app.get("/api/v1/audits/{case_id}/actions")
    def actions(case_id: str):
        items = call(runtime.list_actions, case_id)
        return {"actions": [x.model_dump(mode="json") for x in items]}

    @app.post("/api/v1/audits/{case_id}/plan")
    def plan_next_actions(case_id: str, req: PlanNextActionsRequest):
        return call(
            runtime.plan_next_actions, case_id,
            remaining_time_minutes=req.remaining_time_minutes,
            max_action_cost=req.max_action_cost,
            critical_unknowns=req.critical_unknowns,
        )

    @app.post("/api/v1/audits/{case_id}/sampling/plan")
    def plan_sampling(case_id: str, req: SamplingPlanRequest):
        call(runtime._require_case, case_id)
        plan = sampling_planner.plan(
            case_id=case_id, population_size=req.population_size,
            current_sample_size=req.current_sample_size, high_risk=req.high_risk,
            recurrence_signal=req.recurrence_signal, stale_periods=req.stale_periods,
            target_entity_id=req.target_entity_id,
        )
        return plan.model_dump(mode="json")

    @app.get("/api/v1/audits/{case_id}/graph")
    def graph(case_id: str):
        return call(runtime.graph_summary, case_id)


    @app.post("/api/v1/audits/{case_id}/sources/ingest")
    def ingest_source(case_id: str, req: IngestSourceRequest):
        result = call(
            perception.ingest_file, req.path, source_id=req.source_id,
            organization_id=req.organization_id, audit_case_id=case_id,
            requirement_id=req.requirement_id, controlled=req.controlled,
            version=req.version, authority=req.authority, patterns=req.patterns,
        )
        return {
            "source": result["source"].model_dump(mode="json"),
            "span_count": result["span_count"],
            "chunk_count": result["chunk_count"],
            "candidate_count": result["candidate_count"],
        }

    @app.post("/api/v1/audits/{case_id}/retrieve")
    def retrieve(case_id: str, req: RetrievalRequest):
        hits = call(
            perception.search, case_id, req.query, top_k=req.top_k,
            allowed_source_ids=set(req.allowed_source_ids) if req.allowed_source_ids else None,
            requirement_ids=set(req.requirement_ids) if req.requirement_ids else None,
            metadata_filters=req.metadata_filters,
        )
        return {"hits": [h.__dict__ for h in hits]}

    @app.post("/api/v1/audits/{case_id}/candidates/{candidate_id}/promote")
    def promote_candidate(case_id: str, candidate_id: str):
        result = call(perception.promote_candidate, candidate_id)
        if result.evidence is None:
            raise HTTPException(status_code=409, detail=result.reason)
        if result.evidence.audit_case_id != case_id:
            raise HTTPException(status_code=422, detail="candidate belongs to different audit case")
        snapshot = call(runtime.ingest_evidence, result.evidence)
        return {
            "status": result.reason,
            "evidence": result.evidence.model_dump(mode="json"),
            "world_snapshot_id": snapshot.snapshot_id,
        }

    @app.post("/api/v1/audits/{case_id}/decision")
    def decision(case_id: str, req: DecisionRequest):
        return call(runtime.make_decision, case_id, req.candidate, req.context)


    @app.post("/api/v1/organizations/{organization_id}/temporal/facts")
    def record_temporal_fact(organization_id: str, req: RecordTemporalFactRequest):
        if req.fact.organization_id != organization_id:
            raise HTTPException(status_code=422, detail="organization mismatch")
        item = call(temporal.record_fact, req.fact)
        return {"fact": item.model_dump(mode="json")}

    @app.post("/api/v1/organizations/{organization_id}/world/as-of")
    def world_as_of(organization_id: str, req: AsOfWorldRequest):
        facts = call(temporal.as_of, organization_id, valid_at=req.valid_at, known_at=req.known_at)
        return {"facts": [x.model_dump(mode="json") for x in facts]}

    @app.post("/api/v1/organizations/{organization_id}/recurrence")
    def assess_recurrence(organization_id: str, req: RecurrenceRequest):
        item = call(temporal.assess_recurrence, recurrence_id=req.recurrence_id, organization_id=organization_id, requirement_id=req.requirement_id, prior_finding_id=req.prior_finding_id, current_finding_id=req.current_finding_id, current_observed_at=req.current_observed_at, prior_ca=req.prior_ca, same_or_equivalent_failure=req.same_or_equivalent_failure, representative_scope_confirmed=req.representative_scope_confirmed, evidence_ids=req.evidence_ids)
        return item.model_dump(mode="json")

    return app
