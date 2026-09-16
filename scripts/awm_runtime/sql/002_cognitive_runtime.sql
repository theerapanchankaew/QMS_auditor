-- AIAS AWM v0.4 cognitive runtime extension (PostgreSQL target)
CREATE TABLE IF NOT EXISTS audit_cases (
    audit_case_id varchar(64) PRIMARY KEY,
    organization_id varchar(64) NOT NULL,
    standard_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    audit_type varchar(40) NOT NULL,
    scope jsonb NOT NULL DEFAULT '{}'::jsonb,
    world_snapshot_id varchar(128),
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS atomic_requirements (
    requirement_id varchar(64) PRIMARY KEY,
    standard_id varchar(64) NOT NULL,
    clause varchar(32) NOT NULL,
    subject varchar(128) NOT NULL,
    obligation varchar(128) NOT NULL,
    object_name text NOT NULL,
    condition_text text,
    qualifier text,
    applicability_rule_id varchar(64),
    semantic_category varchar(32) NOT NULL,
    evidence_expectations jsonb NOT NULL DEFAULT '[]'::jsonb,
    failure_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
    negative_inference_rules jsonb NOT NULL DEFAULT '[]'::jsonb,
    version varchar(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS hypotheses (
    hypothesis_id varchar(64) PRIMARY KEY,
    audit_case_id varchar(64) NOT NULL,
    hypothesis_type varchar(40) NOT NULL,
    statement text NOT NULL,
    requirement_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    supporting_evidence_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    contradicting_evidence_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    status varchar(24) NOT NULL,
    unresolved_questions jsonb NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS audit_actions (
    action_id varchar(64) PRIMARY KEY,
    audit_case_id varchar(64) NOT NULL,
    action_type varchar(40) NOT NULL,
    target_requirement_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    target_entity_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    rationale text NOT NULL,
    expected_information_gain double precision,
    cost_score double precision,
    priority_score double precision,
    status varchar(24) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_cases_org ON audit_cases(organization_id);
CREATE INDEX IF NOT EXISTS idx_atomic_requirement_clause ON atomic_requirements(standard_id, clause);
CREATE INDEX IF NOT EXISTS idx_hypothesis_case ON hypotheses(audit_case_id);
CREATE INDEX IF NOT EXISTS idx_action_case ON audit_actions(audit_case_id);
