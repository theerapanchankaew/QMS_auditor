from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from aias_awm.domain.models import AuditAction, StrictModel


class PlanningContext(StrictModel):
    audit_case_id: str
    unresolved_requirement_ids: list[str] = Field(default_factory=list)
    unresolved_hypothesis_ids: list[str] = Field(default_factory=list)
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    stale_evidence_ids: list[str] = Field(default_factory=list)
    sample_population_size: int | None = Field(default=None, ge=0)
    current_sample_size: int | None = Field(default=None, ge=0)
    remaining_time_minutes: float | None = Field(default=None, ge=0.0)
    max_action_cost: float | None = Field(default=None, ge=0.0)
    decision_ready: bool = False
    critical_unknowns: list[str] = Field(default_factory=list)
    created_at: datetime


class ActionScore(StrictModel):
    action_id: str
    information_gain: float = Field(ge=0.0, le=1.0)
    requirement_coverage: float = Field(ge=0.0, le=1.0)
    evidence_strength: float = Field(ge=0.0, le=1.0)
    contradiction_reduction: float = Field(ge=0.0, le=1.0)
    temporal_relevance: float = Field(ge=0.0, le=1.0)
    acquisition_cost: float = Field(ge=0.0)
    risk_weight: float = Field(default=1.0, ge=0.0)
    utility: float
    admissible: bool = True
    blocked_reason: str | None = None


class PlannedAction(StrictModel):
    action: AuditAction
    score: ActionScore


class PlanningDecision(StrictModel):
    audit_case_id: str
    policy_version: str
    ranked_actions: list[PlannedAction] = Field(default_factory=list)
    selected_action_id: str | None = None
    stop_decision: Literal["CONTINUE", "STOP_DECISION_READY", "STOP_BUDGET", "ESCALATE_HUMAN"]
    rationale: str
    created_at: datetime


class SamplingPlan(StrictModel):
    audit_case_id: str
    target_entity_id: str | None = None
    population_size: int = Field(ge=0)
    current_sample_size: int = Field(ge=0)
    additional_sample_size: int = Field(ge=0)
    strategy: Literal["RISK_BASED", "TEMPORAL", "RECURRENCE_TARGETED", "CONTRADICTION_TARGETED"]
    periods: list[str] = Field(default_factory=list)
    rationale: str


class NextActionEvaluation(StrictModel):
    case_id: str
    predicted_action_types: list[str]
    acceptable_gold_action_types: list[str]
    matched: bool
    reciprocal_rank: float = Field(ge=0.0, le=1.0)
