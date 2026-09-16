from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from aias_awm.domain.models import EvidenceItem, EpistemicState, SourcePointer
from aias_awm.perception.models import EvidenceCandidate, CandidateState
from aias_awm.provenance import ProvenanceVerifier, ControlledSourceRegistry


@dataclass(frozen=True)
class PromotionResult:
    evidence: EvidenceItem | None
    reason: str


class EvidencePromotionService:
    """Promotes candidate to PRESENTED evidence only after provenance validation.

    VERIFIED evidence still requires explicit human/system verification; retrieval or
    extraction alone never confers VERIFIED status.
    """
    def __init__(self, registry: ControlledSourceRegistry, verifier: ProvenanceVerifier):
        self.registry = registry
        self.verifier = verifier

    def promote_presented(self, candidate: EvidenceCandidate) -> PromotionResult:
        checked = self.verifier.verify_candidate(candidate)
        if not checked.verified:
            return PromotionResult(None, "PROVENANCE_INVALID:" + ";".join(checked.failures))
        pointers: list[SourcePointer] = []
        for span_id in candidate.span_ids:
            span = self.registry.get_span(span_id)
            doc = self.registry.get_document(candidate.source_id)
            pointers.append(SourcePointer(
                source_id=candidate.source_id, source_version=doc.version if doc else None,
                page=span.page if span else None, cell_or_range=span.cell_range if span else None,
                char_start=span.char_start if span else None, char_end=span.char_end if span else None,
                source_hash=doc.sha256 if doc else None,
                section=(span.sheet if span and span.sheet else None),
            ))
        evidence = EvidenceItem(
            evidence_id="EV-" + candidate.candidate_id.removeprefix("CAND-"),
            organization_id=candidate.organization_id,
            audit_case_id=candidate.audit_case_id,
            evidence_type="document",
            assertion=candidate.assertion,
            normalized_fact=candidate.normalized_fact,
            epistemic_state=EpistemicState.PRESENTED,
            observed_at=candidate.created_at,
            provenance=pointers,
            related_requirement_ids=candidate.related_requirement_ids,
            confidence=candidate.extraction_confidence,
            metadata={"candidate_id": candidate.candidate_id, **candidate.metadata},
        )
        return PromotionResult(evidence, "PROMOTED_TO_PRESENTED")

    def verify(self, evidence: EvidenceItem, *, verified_by: str) -> EvidenceItem:
        # Explicit authority transition. No silent automatic verification.
        return evidence.model_copy(update={
            "epistemic_state": EpistemicState.VERIFIED,
            "verified_by": verified_by,
        })
