from __future__ import annotations

from sqlalchemy import Table, Column, String, DateTime, JSON, Float, Boolean

from .tables import metadata

planning_runs = Table(
    "planning_runs", metadata,
    Column("planning_run_id", String(64), primary_key=True),
    Column("audit_case_id", String(64), nullable=False, index=True),
    Column("policy_version", String(32), nullable=False),
    Column("selected_action_id", String(64), nullable=True),
    Column("stop_decision", String(32), nullable=False),
    Column("rationale", String, nullable=False),
    Column("context_json", JSON, nullable=False),
    Column("decision_json", JSON, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

action_scores = Table(
    "action_scores", metadata,
    Column("score_id", String(96), primary_key=True),
    Column("planning_run_id", String(64), nullable=False, index=True),
    Column("action_id", String(64), nullable=False, index=True),
    Column("utility", Float, nullable=False),
    Column("information_gain", Float, nullable=False),
    Column("requirement_coverage", Float, nullable=False),
    Column("evidence_strength", Float, nullable=False),
    Column("contradiction_reduction", Float, nullable=False),
    Column("temporal_relevance", Float, nullable=False),
    Column("acquisition_cost", Float, nullable=False),
    Column("risk_weight", Float, nullable=False),
    Column("admissible", Boolean, nullable=False),
    Column("blocked_reason", String(128), nullable=True),
)
