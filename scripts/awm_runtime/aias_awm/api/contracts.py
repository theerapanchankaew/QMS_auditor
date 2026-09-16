from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from aias_awm.domain.models import AuditCase, AtomicRequirement, EvidenceItem


class StrictAPIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateCaseRequest(StrictAPIModel):
    case: AuditCase


class RegisterRequirementRequest(StrictAPIModel):
    requirement: AtomicRequirement


class IngestEvidenceRequest(StrictAPIModel):
    evidence: EvidenceItem


class ReasonRequest(StrictAPIModel):
    requirement_ids: list[str] = Field(min_length=1)


class DecisionRequest(StrictAPIModel):
    candidate: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)

from datetime import datetime
from aias_awm.temporal.models import TemporalFact, CorrectiveActionLink

class RecordTemporalFactRequest(StrictAPIModel):
    fact: TemporalFact

class AsOfWorldRequest(StrictAPIModel):
    valid_at: datetime
    known_at: datetime | None = None

class RecurrenceRequest(StrictAPIModel):
    recurrence_id: str
    requirement_id: str
    prior_finding_id: str
    current_finding_id: str | None = None
    current_observed_at: datetime
    prior_ca: CorrectiveActionLink | None = None
    same_or_equivalent_failure: bool
    representative_scope_confirmed: bool = False
    evidence_ids: list[str] = Field(default_factory=list)

class PlanNextActionsRequest(StrictAPIModel):
    remaining_time_minutes: float | None = Field(default=None, ge=0.0)
    max_action_cost: float | None = Field(default=None, ge=0.0)
    critical_unknowns: list[str] = Field(default_factory=list)


class SamplingPlanRequest(StrictAPIModel):
    population_size: int = Field(ge=0)
    current_sample_size: int = Field(ge=0)
    high_risk: bool = False
    recurrence_signal: bool = False
    stale_periods: list[str] = Field(default_factory=list)
    target_entity_id: str | None = None
