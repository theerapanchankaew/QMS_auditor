from __future__ import annotations

from sqlalchemy import Table, Column, String, Text, DateTime, Boolean, JSON, ForeignKey, UniqueConstraint
from .tables import metadata


temporal_facts = Table(
    "temporal_facts", metadata,
    Column("fact_id", String(128), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("entity_id", String(128), nullable=False, index=True),
    Column("fact_type", String(96), nullable=False, index=True),
    Column("value", JSON, nullable=False),
    Column("valid_from", DateTime(timezone=True), nullable=False, index=True),
    Column("valid_to", DateTime(timezone=True), nullable=True, index=True),
    Column("recorded_at", DateTime(timezone=True), nullable=False, index=True),
    Column("supersedes_fact_id", String(128), nullable=True),
    Column("source_evidence_ids", JSON, nullable=False, default=list),
    Column("state", String(24), nullable=False, default="ACTIVE"),
    Column("metadata_json", JSON, nullable=False, default=dict),
)

corrective_action_links = Table(
    "corrective_action_links", metadata,
    Column("ca_id", String(128), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("finding_id", String(128), nullable=False, index=True),
    Column("requirement_id", String(128), nullable=False, index=True),
    Column("process_id", String(128), nullable=True, index=True),
    Column("raised_at", DateTime(timezone=True), nullable=False),
    Column("correction_completed_at", DateTime(timezone=True), nullable=True),
    Column("root_cause_completed_at", DateTime(timezone=True), nullable=True),
    Column("action_completed_at", DateTime(timezone=True), nullable=True),
    Column("effectiveness_verified_at", DateTime(timezone=True), nullable=True),
    Column("effectiveness_result", String(24), nullable=False, default="NOT_VERIFIED"),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Column("source_evidence_ids", JSON, nullable=False, default=list),
)

recurrence_assessments = Table(
    "recurrence_assessments", metadata,
    Column("recurrence_id", String(128), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("requirement_id", String(128), nullable=False, index=True),
    Column("prior_finding_id", String(128), nullable=False),
    Column("current_finding_id", String(128), nullable=True),
    Column("prior_ca_id", String(128), nullable=True),
    Column("current_observed_at", DateTime(timezone=True), nullable=False),
    Column("same_or_equivalent_failure", Boolean, nullable=False),
    Column("prior_effectiveness_verified", Boolean, nullable=False),
    Column("representative_scope_confirmed", Boolean, nullable=False, default=False),
    Column("recurrence_proven", Boolean, nullable=False, default=False),
    Column("m5_eligible", Boolean, nullable=False, default=False),
    Column("rationale", Text, nullable=False),
    Column("evidence_ids", JSON, nullable=False, default=list),
)

temporal_drift_events = Table(
    "temporal_drift_events", metadata,
    Column("drift_id", String(128), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("detected_at", DateTime(timezone=True), nullable=False),
    Column("drift_type", String(48), nullable=False, index=True),
    Column("severity", String(16), nullable=False),
    Column("entity_ids", JSON, nullable=False, default=list),
    Column("requirement_ids", JSON, nullable=False, default=list),
    Column("details", JSON, nullable=False, default=dict),
)
