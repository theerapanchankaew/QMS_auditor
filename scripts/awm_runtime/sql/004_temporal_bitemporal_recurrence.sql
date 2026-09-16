-- AIAS AWM v0.6 temporal/bitemporal foundation (PostgreSQL target)

CREATE TABLE IF NOT EXISTS temporal_facts (
    fact_id VARCHAR(128) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    fact_type VARCHAR(96) NOT NULL,
    value JSONB NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    recorded_at TIMESTAMPTZ NOT NULL,
    supersedes_fact_id VARCHAR(128),
    source_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    state VARCHAR(24) NOT NULL DEFAULT 'ACTIVE',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE INDEX IF NOT EXISTS ix_temporal_facts_org_valid
    ON temporal_facts (organization_id, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS ix_temporal_facts_entity_type
    ON temporal_facts (organization_id, entity_id, fact_type);
CREATE INDEX IF NOT EXISTS ix_temporal_facts_recorded_at
    ON temporal_facts (organization_id, recorded_at);

CREATE TABLE IF NOT EXISTS corrective_action_links (
    ca_id VARCHAR(128) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL,
    finding_id VARCHAR(128) NOT NULL,
    requirement_id VARCHAR(128) NOT NULL,
    process_id VARCHAR(128),
    raised_at TIMESTAMPTZ NOT NULL,
    correction_completed_at TIMESTAMPTZ,
    root_cause_completed_at TIMESTAMPTZ,
    action_completed_at TIMESTAMPTZ,
    effectiveness_verified_at TIMESTAMPTZ,
    effectiveness_result VARCHAR(24) NOT NULL DEFAULT 'NOT_VERIFIED',
    closed_at TIMESTAMPTZ,
    source_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_ca_requirement
    ON corrective_action_links (organization_id, requirement_id, raised_at);

CREATE TABLE IF NOT EXISTS recurrence_assessments (
    recurrence_id VARCHAR(128) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL,
    requirement_id VARCHAR(128) NOT NULL,
    prior_finding_id VARCHAR(128) NOT NULL,
    current_finding_id VARCHAR(128),
    prior_ca_id VARCHAR(128),
    current_observed_at TIMESTAMPTZ NOT NULL,
    same_or_equivalent_failure BOOLEAN NOT NULL,
    prior_effectiveness_verified BOOLEAN NOT NULL,
    representative_scope_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_proven BOOLEAN NOT NULL DEFAULT FALSE,
    m5_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    rationale TEXT NOT NULL,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS temporal_drift_events (
    drift_id VARCHAR(128) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    drift_type VARCHAR(48) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    entity_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);
