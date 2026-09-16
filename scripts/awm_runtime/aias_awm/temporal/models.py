from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from aias_awm.domain.models import StrictModel


class TemporalState(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN = "UNKNOWN"


class TemporalFact(StrictModel):
    fact_id: str
    organization_id: str
    entity_id: str
    fact_type: str
    value: dict[str, Any]
    valid_from: datetime
    valid_to: datetime | None = None
    recorded_at: datetime
    supersedes_fact_id: str | None = None
    source_evidence_ids: list[str] = Field(default_factory=list)
    state: TemporalState = TemporalState.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_interval(self):
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be greater than valid_from")
        return self


class CorrectiveActionLink(StrictModel):
    ca_id: str
    organization_id: str
    finding_id: str
    requirement_id: str
    process_id: str | None = None
    raised_at: datetime
    correction_completed_at: datetime | None = None
    root_cause_completed_at: datetime | None = None
    action_completed_at: datetime | None = None
    effectiveness_verified_at: datetime | None = None
    effectiveness_result: Literal["EFFECTIVE", "INEFFECTIVE", "NOT_VERIFIED"] = "NOT_VERIFIED"
    closed_at: datetime | None = None
    source_evidence_ids: list[str] = Field(default_factory=list)


class RecurrenceAssessment(StrictModel):
    recurrence_id: str
    organization_id: str
    requirement_id: str
    prior_finding_id: str
    current_finding_id: str | None = None
    prior_ca_id: str | None = None
    current_observed_at: datetime
    same_or_equivalent_failure: bool
    prior_effectiveness_verified: bool
    representative_scope_confirmed: bool = False
    recurrence_proven: bool = False
    m5_eligible: bool = False
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)


class AsOfQuery(StrictModel):
    organization_id: str
    valid_at: datetime
    known_at: datetime | None = None
    entity_ids: list[str] = Field(default_factory=list)
    fact_types: list[str] = Field(default_factory=list)


class TemporalDriftEvent(StrictModel):
    drift_id: str
    organization_id: str
    detected_at: datetime
    drift_type: Literal[
        "WORLD_STATE_STALE",
        "SOURCE_STATE_DIVERGENCE",
        "TEMPORAL_CONTRADICTION",
        "LATE_ARRIVING_EVIDENCE",
        "RECURRENCE_SIGNAL",
    ]
    severity: Literal["INFO", "WARN", "ALERT"]
    entity_ids: list[str] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
