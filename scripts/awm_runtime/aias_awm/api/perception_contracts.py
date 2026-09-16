from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class IngestSourceRequest(StrictModel):
    path: str
    source_id: str
    organization_id: str
    requirement_id: str | None = None
    controlled: bool = True
    version: str | None = None
    authority: str | None = None
    patterns: dict[str, list[str]] = Field(default_factory=dict)

class RetrievalRequest(StrictModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    allowed_source_ids: list[str] | None = None
    requirement_ids: list[str] | None = None
    metadata_filters: dict[str, str] = Field(default_factory=dict)
