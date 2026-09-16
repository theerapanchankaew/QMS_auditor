from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import insert, select, delete

from aias_awm.planning.models import PlanningContext, PlanningDecision
from .planning_tables import planning_runs, action_scores


class PlanningDecisionRepository:
    def __init__(self, db) -> None:
        self.db = db

    def save(self, run_id: str, context: PlanningContext, decision: PlanningDecision) -> None:
        with self.db.connect() as conn:
            conn.execute(delete(action_scores).where(action_scores.c.planning_run_id == run_id))
            conn.execute(delete(planning_runs).where(planning_runs.c.planning_run_id == run_id))
            conn.execute(insert(planning_runs).values(
                planning_run_id=run_id,
                audit_case_id=decision.audit_case_id,
                policy_version=decision.policy_version,
                selected_action_id=decision.selected_action_id,
                stop_decision=decision.stop_decision,
                rationale=decision.rationale,
                context_json=context.model_dump(mode="json"),
                decision_json=decision.model_dump(mode="json"),
                created_at=decision.created_at,
            ))
            for item in decision.ranked_actions:
                s = item.score
                conn.execute(insert(action_scores).values(
                    score_id=f"{run_id}:{s.action_id}",
                    planning_run_id=run_id,
                    action_id=s.action_id,
                    utility=s.utility,
                    information_gain=s.information_gain,
                    requirement_coverage=s.requirement_coverage,
                    evidence_strength=s.evidence_strength,
                    contradiction_reduction=s.contradiction_reduction,
                    temporal_relevance=s.temporal_relevance,
                    acquisition_cost=s.acquisition_cost,
                    risk_weight=s.risk_weight,
                    admissible=s.admissible,
                    blocked_reason=s.blocked_reason,
                ))

    def latest_for_case(self, case_id: str) -> dict | None:
        with self.db.connect() as conn:
            row = conn.execute(
                select(planning_runs).where(planning_runs.c.audit_case_id == case_id).order_by(planning_runs.c.created_at.desc()).limit(1)
            ).mappings().first()
            return dict(row) if row else None
