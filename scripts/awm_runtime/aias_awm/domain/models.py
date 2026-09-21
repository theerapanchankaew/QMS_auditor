from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class EpistemicState(str, Enum):
    UNKNOWN = "UNKNOWN"
    CLAIMED = "CLAIMED"
    PRESENTED = "PRESENTED"
    PARSED = "PARSED"
    PARTIAL = "PARTIAL"
    CORROBORATED = "CORROBORATED"
    VERIFIED = "VERIFIED"
    CONTRADICTORY = "CONTRADICTORY"
    INVALID = "INVALID"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


class RequirementState(str, Enum):
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    SATISFIED = "SATISFIED"
    BREACH_PROVEN = "BREACH_PROVEN"
    CONTRADICTORY = "CONTRADICTORY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class Verdict(str, Enum):
    COMPLIED = "Complied"
    OFI = "OFI"
    NONCOMPLIED = "Noncomplied"
    INSUFFICIENT_EVIDENCE = "InsufficientEvidence"
    REVIEW_REQUIRED = "ReviewRequired"


class NCClass(str, Enum):
    MAJOR = "Major"
    MINOR = "Minor"


class SourcePointer(StrictModel):
    source_id: str
    source_version: str | None = None
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    record_id: str | None = None
    cell_or_range: str | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    source_hash: str | None = None


class EvidenceItem(StrictModel):
    evidence_id: str
    organization_id: str
    audit_case_id: str | None = None
    process_id: str | None = None
    evidence_type: Literal[
        "document",
        "record",
        "interview",
        "observation",
        "measurement",
        "system_log",
        "external_source",
    ]
    assertion: str
    normalized_fact: str | None = None
    epistemic_state: EpistemicState
    observed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    provenance: list[SourcePointer] = Field(default_factory=list)
    related_requirement_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    verified_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceExpectation(StrictModel):
    evidence_type: str
    minimum_strength: Literal[
        "claim",
        "documented",
        "implemented",
        "recorded",
        "verified",
        "effectiveness",
    ]
    mandatory: bool = True


class AtomicRequirement(StrictModel):
    requirement_id: str
    standard_id: str
    clause: str
    subject: str
    obligation: str
    object: str
    condition: str | None = None
    qualifier: str | None = None
    applicability_rule_id: str | None = None
    semantic_category: Literal["D2_SAFE", "M4_MANDATORY", "AMBIGUOUS"]
    evidence_expectations: list[EvidenceExpectation]
    failure_patterns: list[str] = Field(default_factory=list)
    negative_inference_rules: list[str] = Field(default_factory=list)
    version: str


class RequirementAssessment(StrictModel):
    assessment_id: str
    audit_case_id: str
    requirement_id: str
    applicability: Literal["APPLICABLE", "NOT_APPLICABLE", "UNRESOLVED"]
    state: RequirementState
    positive_evidence_ids: list[str] = Field(default_factory=list)
    negative_evidence_ids: list[str] = Field(default_factory=list)
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    coverage_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    breach_proven: bool = False
    effectiveness_proven: bool | None = None
    reasoning_candidate: str | None = None
    updated_at: datetime


class EntityState(StrictModel):
    entity_id: str
    entity_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    effective_from: datetime
    effective_to: datetime | None = None


class WorldSnapshot(StrictModel):
    snapshot_id: str
    organization_id: str
    as_of: datetime
    process_states: list[EntityState] = Field(default_factory=list)
    control_states: list[EntityState] = Field(default_factory=list)
    risk_states: list[EntityState] = Field(default_factory=list)
    opportunity_states: list[EntityState] = Field(default_factory=list)
    requirement_states: list[RequirementAssessment] = Field(default_factory=list)
    hypothesis_states: list[AuditHypothesis] = Field(default_factory=list)
    action_states: list[AuditAction] = Field(default_factory=list)
    source_manifest_hash: str
    rule_pack_hash: str
    created_from_event_seq: int = Field(ge=0)


class WorldEvent(StrictModel):
    event_id: str
    organization_id: str
    sequence_no: int = Field(ge=0)
    event_type: str
    event_time: datetime
    recorded_at: datetime
    actor_id: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    source_evidence_ids: list[str] = Field(default_factory=list)
    prior_state_hash: str | None = None
    resulting_state_hash: str | None = None


class AuditHypothesis(StrictModel):
    hypothesis_id: str
    audit_case_id: str
    hypothesis_type: Literal[
        "CONFORMITY",
        "BREACH",
        "INSUFFICIENT_EVIDENCE",
        "SYSTEMIC_FAILURE",
        "INEFFECTIVE_CONTROL",
        "RECURRENCE",
    ]
    statement: str
    requirement_ids: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    status: Literal["PROPOSED", "SUPPORTED", "WEAKENED", "REFUTED", "UNRESOLVED"]
    unresolved_questions: list[str] = Field(default_factory=list)
    possible_worlds_dimensions: dict[str, list[str]] | None = None
    known_facts: dict[str, str] = Field(default_factory=dict)


class AuditAction(StrictModel):
    action_id: str
    audit_case_id: str
    action_type: Literal[
        "REQUEST_DOCUMENT",
        "REQUEST_RECORD",
        "ASK_INTERVIEW",
        "OBSERVE_PROCESS",
        "EXPAND_SAMPLE",
        "TRACE_TRANSACTION",
        "VERIFY_APPROVAL",
        "VERIFY_VERSION",
        "VERIFY_EFFECTIVENESS",
        "CHECK_RECURRENCE",
        "CROSS_CHECK",
        "ESCALATE_HUMAN",
        "STOP",
    ]
    target_requirement_ids: list[str] = Field(default_factory=list)
    target_entity_ids: list[str] = Field(default_factory=list)
    rationale: str
    expected_information_gain: float | None = Field(default=None, ge=0.0, le=1.0)
    cost_score: float | None = Field(default=None, ge=0.0)
    priority_score: float | None = Field(default=None, ge=0.0)
    status: Literal["PROPOSED", "APPROVED", "EXECUTED", "CANCELLED"]


class GateResult(StrictModel):
    gate_id: str
    gate_version: str
    result: Literal["PASS", "FAIL", "BLOCK", "PENDING", "NA"]
    reason_code: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class GateTrace(StrictModel):
    trace_id: str
    audit_case_id: str
    world_snapshot_id: str
    requirement_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    gates: list[GateResult] = Field(default_factory=list)
    candidate_verdict: Verdict
    candidate_nc_class: NCClass | None = None
    created_at: datetime


class AuditCase(StrictModel):
    audit_case_id: str
    organization_id: str
    standard_ids: list[str]
    audit_type: Literal[
        "document_review",
        "record_sampling",
        "interview",
        "observation",
        "performance_data_review",
        "scenario_assessment",
        "initial",
        "surveillance",
        "recertification",
    ]
    scope: dict[str, Any] = Field(default_factory=dict)
    world_snapshot_id: str | None = None
    created_at: datetime


class ReasoningProposal(StrictModel):
    mapped_requirement_ids: list[str] = Field(default_factory=list)
    evidence_interpretations: list[dict[str, Any]] = Field(default_factory=list)
    proposed_hypotheses: list[AuditHypothesis] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    proposed_actions: list[AuditAction] = Field(default_factory=list)
    candidate_assessments: list[RequirementAssessment] = Field(default_factory=list)
    candidate_verdict: Verdict | None = None
    candidate_nc_class: NCClass | None = None
