from __future__ import annotations

from pathlib import Path

from aias_awm.persistence.source_repositories import SourceDocumentRepository, SourceSpanRepository, DocumentChunkRepository, EvidenceCandidateRepository
from aias_awm.provenance import ControlledSourceRegistry, ProvenanceVerifier
from aias_awm.retrieval import HybridRetriever
from .parsers import parser_for_path
from .chunking import SpanChunker
from .extraction import RuleBasedEvidenceExtractor
from .promotion import EvidencePromotionService


class PersistentPerceptionRuntime:
    """Persistent source ingestion/retrieval boundary.

    Retrieval returns candidates only. It never silently promotes retrieved text to VERIFIED evidence.
    """
    def __init__(self, db):
        self.db=db
        self.documents=SourceDocumentRepository(db)
        self.spans=SourceSpanRepository(db)
        self.chunks=DocumentChunkRepository(db)
        self.candidates=EvidenceCandidateRepository(db)

    def ingest_file(self, path: str | Path, *, source_id: str, organization_id: str,
                    audit_case_id: str | None=None, requirement_id: str | None=None,
                    controlled: bool=True, version: str | None=None, authority: str | None=None,
                    patterns: dict[str,list[str]] | None=None) -> dict:
        parsed = parser_for_path(path).parse(path, source_id=source_id, organization_id=organization_id,
                    audit_case_id=audit_case_id, controlled=controlled, version=version, authority=authority)
        chunked = SpanChunker().chunk(source_id, parsed.spans)
        extracted = RuleBasedEvidenceExtractor(patterns).extract(organization_id=organization_id,
                    audit_case_id=audit_case_id, chunks=chunked, requirement_id=requirement_id)
        self.documents.upsert(parsed.document); self.spans.upsert_many(parsed.spans); self.chunks.upsert_many(chunked); self.candidates.upsert_many(extracted)
        return {"source":parsed.document, "span_count":len(parsed.spans), "chunk_count":len(chunked), "candidate_count":len(extracted)}

    def search(self, case_id: str, query: str, *, top_k:int=5, allowed_source_ids:set[str]|None=None,
               requirement_ids:set[str]|None=None, metadata_filters:dict[str,str]|None=None):
        retriever = HybridRetriever(self.chunks.list_for_case(case_id))
        return retriever.search(query, top_k=top_k, allowed_source_ids=allowed_source_ids,
                                requirement_ids=requirement_ids, metadata_filters=metadata_filters)

    def _registry_for_candidate(self, candidate):
        registry=ControlledSourceRegistry()
        doc=self.documents.get(candidate.source_id)
        if doc is None: raise KeyError(f"unknown source: {candidate.source_id}")
        spans=self.spans.list_for_source(candidate.source_id)
        registry.register(doc, spans)
        return registry

    def promote_candidate(self, candidate_id: str):
        candidate=self.candidates.get(candidate_id)
        if candidate is None: raise KeyError(f"unknown candidate: {candidate_id}")
        registry=self._registry_for_candidate(candidate)
        svc=EvidencePromotionService(registry, ProvenanceVerifier(registry))
        return svc.promote_presented(candidate)
