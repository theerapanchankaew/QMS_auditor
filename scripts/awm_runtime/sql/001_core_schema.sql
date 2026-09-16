CREATE TABLE organizations (
    organization_id VARCHAR(64) PRIMARY KEY,
    name TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_cases (
    audit_case_id VARCHAR(64) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL REFERENCES organizations(organization_id),
    audit_type VARCHAR(40) NOT NULL,
    standard_ids JSONB NOT NULL,
    scope JSONB NOT NULL DEFAULT '{}'::jsonb,
    world_snapshot_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE atomic_requirements (
    requirement_id VARCHAR(64) PRIMARY KEY,
    standard_id VARCHAR(64) NOT NULL,
    clause VARCHAR(32) NOT NULL,
    subject TEXT NOT NULL,
    obligation TEXT NOT NULL,
    object TEXT NOT NULL,
    condition TEXT,
    qualifier TEXT,
    applicability_rule_id VARCHAR(64),
    semantic_category VARCHAR(24) NOT NULL,
    evidence_expectations JSONB NOT NULL,
    failure_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
    negative_inference_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    version VARCHAR(32) NOT NULL
);

CREATE TABLE evidence_items (
    evidence_id VARCHAR(64) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL REFERENCES organizations(organization_id),
    audit_case_id VARCHAR(64) REFERENCES audit_cases(audit_case_id),
    process_id VARCHAR(64),
    evidence_type VARCHAR(32) NOT NULL,
    assertion TEXT NOT NULL,
    normalized_fact TEXT,
    epistemic_state VARCHAR(32) NOT NULL,
    observed_at TIMESTAMPTZ,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    confidence NUMERIC(5,4) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    verified_by VARCHAR(128),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE evidence_source_pointers (
    pointer_id BIGSERIAL PRIMARY KEY,
    evidence_id VARCHAR(64) NOT NULL REFERENCES evidence_items(evidence_id) ON DELETE CASCADE,
    source_id VARCHAR(128) NOT NULL,
    source_version VARCHAR(64),
    page INTEGER CHECK (page IS NULL OR page >= 1),
    section TEXT,
    record_id TEXT,
    cell_or_range TEXT,
    char_start INTEGER,
    char_end INTEGER,
    source_hash VARCHAR(128)
);

CREATE TABLE evidence_requirement_links (
    evidence_id VARCHAR(64) NOT NULL REFERENCES evidence_items(evidence_id) ON DELETE CASCADE,
    requirement_id VARCHAR(64) NOT NULL REFERENCES atomic_requirements(requirement_id),
    relation VARCHAR(24) NOT NULL CHECK (relation IN ('SUPPORTS','CONTRADICTS','CORROBORATES','SUPERSEDES')),
    PRIMARY KEY (evidence_id, requirement_id, relation)
);

CREATE TABLE requirement_assessments (
    assessment_id VARCHAR(64) PRIMARY KEY,
    audit_case_id VARCHAR(64) NOT NULL REFERENCES audit_cases(audit_case_id) ON DELETE CASCADE,
    requirement_id VARCHAR(64) NOT NULL REFERENCES atomic_requirements(requirement_id),
    applicability VARCHAR(24) NOT NULL,
    state VARCHAR(32) NOT NULL,
    positive_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    negative_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    contradictory_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    coverage_ratio NUMERIC(5,4) CHECK (coverage_ratio IS NULL OR (coverage_ratio >= 0 AND coverage_ratio <= 1)),
    breach_proven BOOLEAN NOT NULL DEFAULT FALSE,
    effectiveness_proven BOOLEAN,
    reasoning_candidate TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (audit_case_id, requirement_id)
);

CREATE TABLE hypotheses (
    hypothesis_id VARCHAR(64) PRIMARY KEY,
    audit_case_id VARCHAR(64) NOT NULL REFERENCES audit_cases(audit_case_id) ON DELETE CASCADE,
    hypothesis_type VARCHAR(40) NOT NULL,
    statement TEXT NOT NULL,
    requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    supporting_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    contradicting_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(24) NOT NULL,
    unresolved_questions JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE audit_actions (
    action_id VARCHAR(64) PRIMARY KEY,
    audit_case_id VARCHAR(64) NOT NULL REFERENCES audit_cases(audit_case_id) ON DELETE CASCADE,
    action_type VARCHAR(40) NOT NULL,
    target_requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_entity_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    rationale TEXT NOT NULL,
    expected_information_gain NUMERIC(5,4),
    cost_score NUMERIC(12,4),
    priority_score NUMERIC(12,4),
    status VARCHAR(24) NOT NULL
);

CREATE TABLE world_events (
    event_id VARCHAR(64) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL REFERENCES organizations(organization_id),
    sequence_no BIGINT NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    actor_id VARCHAR(64),
    entity_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    prior_state_hash VARCHAR(128),
    resulting_state_hash VARCHAR(128),
    UNIQUE (organization_id, sequence_no)
);

CREATE TABLE world_snapshots (
    snapshot_id VARCHAR(64) PRIMARY KEY,
    organization_id VARCHAR(64) NOT NULL REFERENCES organizations(organization_id),
    as_of TIMESTAMPTZ NOT NULL,
    process_states JSONB NOT NULL DEFAULT '[]'::jsonb,
    control_states JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_states JSONB NOT NULL DEFAULT '[]'::jsonb,
    opportunity_states JSONB NOT NULL DEFAULT '[]'::jsonb,
    requirement_states JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_manifest_hash VARCHAR(128) NOT NULL,
    rule_pack_hash VARCHAR(128) NOT NULL,
    created_from_event_seq BIGINT NOT NULL
);

CREATE TABLE gate_runs (
    gate_run_id VARCHAR(64) PRIMARY KEY,
    audit_case_id VARCHAR(64) NOT NULL REFERENCES audit_cases(audit_case_id),
    world_snapshot_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gate_results (
    gate_result_id BIGSERIAL PRIMARY KEY,
    gate_run_id VARCHAR(64) NOT NULL REFERENCES gate_runs(gate_run_id) ON DELETE CASCADE,
    gate_id VARCHAR(8) NOT NULL,
    gate_version VARCHAR(32) NOT NULL,
    input_hash VARCHAR(128) NOT NULL,
    result VARCHAR(16) NOT NULL,
    reason_code VARCHAR(64),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_evidence_case ON evidence_items(audit_case_id);
CREATE INDEX idx_evidence_org ON evidence_items(organization_id);
CREATE INDEX idx_req_assess_case ON requirement_assessments(audit_case_id);
CREATE INDEX idx_world_event_org_seq ON world_events(organization_id, sequence_no);
CREATE INDEX idx_gate_result_run ON gate_results(gate_run_id);
