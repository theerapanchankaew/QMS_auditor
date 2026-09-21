from __future__ import annotations

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    Integer,
    BigInteger,
    JSON,
    UniqueConstraint,
)

metadata = MetaData()


evidence_items = Table(
    "evidence_items", metadata,
    Column("evidence_id", String(64), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("audit_case_id", String(64), nullable=True, index=True),
    Column("process_id", String(64), nullable=True),
    Column("evidence_type", String(32), nullable=False),
    Column("assertion", Text, nullable=False),
    Column("normalized_fact", Text, nullable=True),
    Column("epistemic_state", String(32), nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=True),
    Column("valid_from", DateTime(timezone=True), nullable=True),
    Column("valid_to", DateTime(timezone=True), nullable=True),
    Column("provenance", JSON, nullable=False, default=list),
    Column("related_requirement_ids", JSON, nullable=False, default=list),
    Column("confidence", Float, nullable=True),
    Column("verified_by", String(128), nullable=True),
    Column("metadata_json", JSON, nullable=False, default=dict),
)

requirement_assessments = Table(
    "requirement_assessments", metadata,
    Column("assessment_id", String(64), primary_key=True),
    Column("audit_case_id", String(64), nullable=False, index=True),
    Column("requirement_id", String(64), nullable=False, index=True),
    Column("applicability", String(24), nullable=False),
    Column("state", String(32), nullable=False),
    Column("positive_evidence_ids", JSON, nullable=False, default=list),
    Column("negative_evidence_ids", JSON, nullable=False, default=list),
    Column("contradictory_evidence_ids", JSON, nullable=False, default=list),
    Column("missing_evidence", JSON, nullable=False, default=list),
    Column("coverage_ratio", Float, nullable=True),
    Column("breach_proven", Boolean, nullable=False, default=False),
    Column("effectiveness_proven", Boolean, nullable=True),
    Column("reasoning_candidate", Text, nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("audit_case_id", "requirement_id", name="uq_case_requirement"),
)

hypotheses = Table(
    "hypotheses", metadata,
    Column("hypothesis_id", String(64), primary_key=True),
    Column("audit_case_id", String(64), nullable=False, index=True),
    Column("hypothesis_type", String(40), nullable=False),
    Column("statement", Text, nullable=False),
    Column("requirement_ids", JSON, nullable=False, default=list),
    Column("supporting_evidence_ids", JSON, nullable=False, default=list),
    Column("contradicting_evidence_ids", JSON, nullable=False, default=list),
    Column("status", String(24), nullable=False),
    Column("unresolved_questions", JSON, nullable=False, default=list),
    Column("possible_worlds_dimensions", JSON, nullable=True),
    Column("known_facts", JSON, nullable=False, default=dict),
)

audit_actions = Table(
    "audit_actions", metadata,
    Column("action_id", String(64), primary_key=True),
    Column("audit_case_id", String(64), nullable=False, index=True),
    Column("action_type", String(40), nullable=False),
    Column("target_requirement_ids", JSON, nullable=False, default=list),
    Column("target_entity_ids", JSON, nullable=False, default=list),
    Column("rationale", Text, nullable=False),
    Column("expected_information_gain", Float, nullable=True),
    Column("cost_score", Float, nullable=True),
    Column("priority_score", Float, nullable=True),
    Column("status", String(24), nullable=False),
)

world_events = Table(
    "world_events", metadata,
    Column("event_id", String(64), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("sequence_no", BigInteger, nullable=False),
    Column("event_type", String(64), nullable=False),
    Column("event_time", DateTime(timezone=True), nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("actor_id", String(64), nullable=True),
    Column("entity_ids", JSON, nullable=False, default=list),
    Column("payload", JSON, nullable=False, default=dict),
    Column("source_evidence_ids", JSON, nullable=False, default=list),
    Column("prior_state_hash", String(128), nullable=True),
    Column("resulting_state_hash", String(128), nullable=True),
    UniqueConstraint("organization_id", "sequence_no", name="uq_org_event_seq"),
)

audit_cases = Table(
    "audit_cases", metadata,
    Column("audit_case_id", String(64), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("standard_ids", JSON, nullable=False, default=list),
    Column("audit_type", String(40), nullable=False),
    Column("scope", JSON, nullable=False, default=dict),
    Column("world_snapshot_id", String(128), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

atomic_requirements = Table(
    "atomic_requirements", metadata,
    Column("requirement_id", String(64), primary_key=True),
    Column("standard_id", String(64), nullable=False, index=True),
    Column("clause", String(32), nullable=False, index=True),
    Column("subject", String(128), nullable=False),
    Column("obligation", String(128), nullable=False),
    Column("object_name", Text, nullable=False),
    Column("condition_text", Text, nullable=True),
    Column("qualifier", Text, nullable=True),
    Column("applicability_rule_id", String(64), nullable=True),
    Column("semantic_category", String(32), nullable=False),
    Column("evidence_expectations", JSON, nullable=False, default=list),
    Column("failure_patterns", JSON, nullable=False, default=list),
    Column("negative_inference_rules", JSON, nullable=False, default=list),
    Column("version", String(32), nullable=False),
)
