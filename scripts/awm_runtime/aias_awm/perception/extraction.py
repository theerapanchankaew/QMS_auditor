from __future__ import annotations

from datetime import datetime, timezone
import re
from aias_awm.perception.models import DocumentChunk, EvidenceCandidate, CandidateState


class RuleBasedEvidenceExtractor:
    """Deterministic baseline extractor used before any LLM extractor is trusted.

    Rules are intentionally transparent and replaceable. LLM extraction can later
    propose candidates against the same EvidenceCandidate contract.
    """
    VERSION = "0.5.0"

    def __init__(self, patterns: dict[str, list[str]] | None = None):
        self.patterns = patterns or {}

    def extract(self, *, organization_id: str, audit_case_id: str | None,
                chunks: list[DocumentChunk], requirement_id: str | None = None) -> list[EvidenceCandidate]:
        out: list[EvidenceCandidate] = []
        pats = self.patterns.get(requirement_id or "", [])
        compiled = [re.compile(p, re.I | re.UNICODE) for p in pats]
        for chunk in chunks:
            if compiled and not any(p.search(chunk.text) for p in compiled):
                continue
            if not chunk.text.strip():
                continue
            assertion = chunk.text.strip()
            cid = f"CAND-{chunk.chunk_id.replace(':','-')}"
            out.append(EvidenceCandidate(
                candidate_id=cid, organization_id=organization_id,
                audit_case_id=audit_case_id, source_id=chunk.source_id,
                span_ids=list(chunk.span_ids), assertion=assertion,
                normalized_fact=None, candidate_state=CandidateState.CANDIDATE,
                evidence_type="document", related_requirement_ids=[requirement_id] if requirement_id else [],
                extraction_confidence=0.60 if compiled else 0.40,
                extractor="rule_based", extractor_version=self.VERSION,
                created_at=datetime.now(timezone.utc), metadata={"chunk_id": chunk.chunk_id}
            ))
        return out
