CREATE TABLE IF NOT EXISTS planning_runs (
    planning_run_id VARCHAR(64) PRIMARY KEY,
    audit_case_id VARCHAR(64) NOT NULL,
    policy_version VARCHAR(32) NOT NULL,
    selected_action_id VARCHAR(64),
    stop_decision VARCHAR(32) NOT NULL,
    rationale TEXT NOT NULL,
    context_json JSONB NOT NULL,
    decision_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_planning_runs_case ON planning_runs(audit_case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS action_scores (
    score_id VARCHAR(96) PRIMARY KEY,
    planning_run_id VARCHAR(64) NOT NULL,
    action_id VARCHAR(64) NOT NULL,
    utility DOUBLE PRECISION NOT NULL,
    information_gain DOUBLE PRECISION NOT NULL,
    requirement_coverage DOUBLE PRECISION NOT NULL,
    evidence_strength DOUBLE PRECISION NOT NULL,
    contradiction_reduction DOUBLE PRECISION NOT NULL,
    temporal_relevance DOUBLE PRECISION NOT NULL,
    acquisition_cost DOUBLE PRECISION NOT NULL,
    risk_weight DOUBLE PRECISION NOT NULL,
    admissible BOOLEAN NOT NULL,
    blocked_reason VARCHAR(128)
);
CREATE INDEX IF NOT EXISTS ix_action_scores_run ON action_scores(planning_run_id, utility DESC);
