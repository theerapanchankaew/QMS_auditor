from __future__ import annotations

from sqlalchemy import Table, Column, String, Text, DateTime, Integer, Float, Boolean, JSON, ForeignKey
from .tables import metadata

source_documents = Table(
    "source_documents", metadata,
    Column("source_id", String(128), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("audit_case_id", String(64), nullable=True, index=True),
    Column("title", Text, nullable=False),
    Column("kind", String(24), nullable=False),
    Column("uri", Text, nullable=True),
    Column("version", String(64), nullable=True),
    Column("authority", String(128), nullable=True),
    Column("controlled", Boolean, nullable=False, default=True),
    Column("sha256", String(64), nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Column("metadata_json", JSON, nullable=False, default=dict),
)

source_spans = Table(
    "source_spans", metadata,
    Column("span_id", String(192), primary_key=True),
    Column("source_id", String(128), nullable=False, index=True),
    Column("page", Integer, nullable=True),
    Column("sheet", String(128), nullable=True),
    Column("cell_range", String(64), nullable=True),
    Column("paragraph_index", Integer, nullable=True),
    Column("char_start", Integer, nullable=True),
    Column("char_end", Integer, nullable=True),
    Column("text", Text, nullable=False),
    Column("span_hash", String(64), nullable=False),
    Column("metadata_json", JSON, nullable=False, default=dict),
)

document_chunks = Table(
    "document_chunks", metadata,
    Column("chunk_id", String(192), primary_key=True),
    Column("source_id", String(128), nullable=False, index=True),
    Column("span_ids", JSON, nullable=False, default=list),
    Column("text", Text, nullable=False),
    Column("chunk_hash", String(64), nullable=False),
    Column("ordinal", Integer, nullable=False),
    Column("token_estimate", Integer, nullable=False),
    Column("metadata_json", JSON, nullable=False, default=dict),
)

evidence_candidates = Table(
    "evidence_candidates", metadata,
    Column("candidate_id", String(192), primary_key=True),
    Column("organization_id", String(64), nullable=False, index=True),
    Column("audit_case_id", String(64), nullable=True, index=True),
    Column("source_id", String(128), nullable=False, index=True),
    Column("span_ids", JSON, nullable=False, default=list),
    Column("assertion", Text, nullable=False),
    Column("normalized_fact", Text, nullable=True),
    Column("candidate_state", String(24), nullable=False),
    Column("evidence_type", String(32), nullable=False),
    Column("related_requirement_ids", JSON, nullable=False, default=list),
    Column("extraction_confidence", Float, nullable=False),
    Column("extractor", String(64), nullable=False),
    Column("extractor_version", String(32), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("metadata_json", JSON, nullable=False, default=dict),
)
