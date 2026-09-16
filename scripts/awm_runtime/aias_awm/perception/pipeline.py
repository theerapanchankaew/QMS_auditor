from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from .parsers import parser_for_path, ParseResult
from .chunking import SpanChunker
from .models import DocumentChunk, EvidenceCandidate
from .extraction import RuleBasedEvidenceExtractor
from aias_awm.provenance import ControlledSourceRegistry, ProvenanceVerifier
from .promotion import EvidencePromotionService


@dataclass
class PerceptionResult:
    parse: ParseResult
    chunks: list[DocumentChunk]
    candidates: list[EvidenceCandidate]


class PerceptionPipeline:
    def __init__(self, registry: ControlledSourceRegistry | None = None,
                 chunker: SpanChunker | None = None):
        self.registry = registry or ControlledSourceRegistry()
        self.chunker = chunker or SpanChunker()

    def ingest(self, path: str | Path, *, source_id: str, organization_id: str,
               audit_case_id: str | None = None, requirement_id: str | None = None,
               controlled: bool = True, version: str | None = None,
               authority: str | None = None, patterns: dict[str, list[str]] | None = None) -> PerceptionResult:
        parsed = parser_for_path(path).parse(
            path, source_id=source_id, organization_id=organization_id,
            audit_case_id=audit_case_id, controlled=controlled,
            version=version, authority=authority,
        )
        self.registry.register(parsed.document, parsed.spans)
        chunks = self.chunker.chunk(source_id, parsed.spans)
        extractor = RuleBasedEvidenceExtractor(patterns)
        candidates = extractor.extract(
            organization_id=organization_id, audit_case_id=audit_case_id,
            chunks=chunks, requirement_id=requirement_id,
        )
        return PerceptionResult(parsed, chunks, candidates)

    def promotion_service(self) -> EvidencePromotionService:
        verifier = ProvenanceVerifier(self.registry)
        return EvidencePromotionService(self.registry, verifier)
