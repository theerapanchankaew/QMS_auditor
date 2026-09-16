from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SourceKind(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TEXT = "text"
    JSON = "json"
    SYSTEM = "system"
    OTHER = "other"


class CandidateState(str, Enum):
    RAW = "RAW"
    CANDIDATE = "CANDIDATE"
    PRESENTED = "PRESENTED"
    CORROBORATED = "CORROBORATED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class SourceDocument(StrictModel):
    source_id: str
    organization_id: str
    audit_case_id: str | None = None
    title: str
    kind: SourceKind
    uri: str | None = None
    version: str | None = None
    authority: str | None = None
    controlled: bool = True
    sha256: str
    size_bytes: int = Field(ge=0)
    ingested_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceSpan(StrictModel):
    span_id: str
    source_id: str
    page: int | None = Field(default=None, ge=1)
    sheet: str | None = None
    cell_range: str | None = None
    paragraph_index: int | None = Field(default=None, ge=0)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    text: str
    span_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(StrictModel):
    chunk_id: str
    source_id: str
    span_ids: list[str] = Field(default_factory=list)
    text: str
    chunk_hash: str
    ordinal: int = Field(ge=0)
    token_estimate: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceCandidate(StrictModel):
    candidate_id: str
    organization_id: str
    audit_case_id: str | None = None
    source_id: str
    span_ids: list[str]
    assertion: str
    normalized_fact: str | None = None
    candidate_state: CandidateState = CandidateState.CANDIDATE
    evidence_type: str = "document"
    related_requirement_ids: list[str] = Field(default_factory=list)
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    extractor: str
    extractor_version: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
