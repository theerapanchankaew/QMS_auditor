-- AIAS AWM v0.5 perception/provenance schema
CREATE TABLE IF NOT EXISTS source_documents (
  source_id VARCHAR(128) PRIMARY KEY,
  organization_id VARCHAR(64) NOT NULL,
  audit_case_id VARCHAR(64),
  title TEXT NOT NULL,
  kind VARCHAR(24) NOT NULL,
  uri TEXT,
  version VARCHAR(64),
  authority VARCHAR(128),
  controlled BOOLEAN NOT NULL DEFAULT TRUE,
  sha256 VARCHAR(64) NOT NULL,
  size_bytes INTEGER NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS source_spans (
  span_id VARCHAR(192) PRIMARY KEY,
  source_id VARCHAR(128) NOT NULL,
  page INTEGER,
  sheet VARCHAR(128),
  cell_range VARCHAR(64),
  paragraph_index INTEGER,
  char_start INTEGER,
  char_end INTEGER,
  text TEXT NOT NULL,
  span_hash VARCHAR(64) NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS document_chunks (
  chunk_id VARCHAR(192) PRIMARY KEY,
  source_id VARCHAR(128) NOT NULL,
  span_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  text TEXT NOT NULL,
  chunk_hash VARCHAR(64) NOT NULL,
  ordinal INTEGER NOT NULL,
  token_estimate INTEGER NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS evidence_candidates (
  candidate_id VARCHAR(192) PRIMARY KEY,
  organization_id VARCHAR(64) NOT NULL,
  audit_case_id VARCHAR(64),
  source_id VARCHAR(128) NOT NULL,
  span_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  assertion TEXT NOT NULL,
  normalized_fact TEXT,
  candidate_state VARCHAR(24) NOT NULL,
  evidence_type VARCHAR(32) NOT NULL,
  related_requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  extraction_confidence DOUBLE PRECISION NOT NULL,
  extractor VARCHAR(64) NOT NULL,
  extractor_version VARCHAR(32) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_source_documents_case ON source_documents(audit_case_id);
CREATE INDEX IF NOT EXISTS ix_source_spans_source ON source_spans(source_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_source ON document_chunks(source_id);
CREATE INDEX IF NOT EXISTS ix_evidence_candidates_case ON evidence_candidates(audit_case_id);
