from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from aias_awm.domain.models import EvidenceItem, EpistemicState


@dataclass(frozen=True)
class EvidenceBundle:
    requirement_id: str
    evidence: tuple[EvidenceItem, ...]
    positive_ids: tuple[str, ...]
    negative_ids: tuple[str, ...]
    contradictory_ids: tuple[str, ...]
    verified_ids: tuple[str, ...]
    invalid_ids: tuple[str, ...]

    @property
    def has_verified(self) -> bool:
        return bool(self.verified_ids)

    @property
    def has_contradiction(self) -> bool:
        return bool(self.contradictory_ids)


class EvidenceReconciliationEngine:
    """Deterministically groups evidence by atomic requirement and resolves basic epistemic classes.

    This engine does not decide conformity. It only creates a controlled evidence bundle.
    Evidence polarity is read from metadata['polarity'] where values are support|negative|contradict.
    If omitted, evidence is treated as supporting evidence.
    """

    def reconcile(self, evidence_items: list[EvidenceItem]) -> dict[str, EvidenceBundle]:
        grouped: dict[str, list[EvidenceItem]] = defaultdict(list)
        for item in evidence_items:
            for requirement_id in item.related_requirement_ids:
                grouped[requirement_id].append(item)

        output: dict[str, EvidenceBundle] = {}
        for requirement_id, items in grouped.items():
            positive: list[str] = []
            negative: list[str] = []
            contradictory: list[str] = []
            verified: list[str] = []
            invalid: list[str] = []

            for item in items:
                polarity = str(item.metadata.get("polarity", "support")).lower()
                if item.epistemic_state in {EpistemicState.INVALID, EpistemicState.SUPERSEDED}:
                    invalid.append(item.evidence_id)
                if item.epistemic_state in {EpistemicState.VERIFIED, EpistemicState.CORROBORATED}:
                    verified.append(item.evidence_id)
                if item.epistemic_state == EpistemicState.CONTRADICTORY or polarity == "contradict":
                    contradictory.append(item.evidence_id)
                elif polarity == "negative":
                    negative.append(item.evidence_id)
                else:
                    positive.append(item.evidence_id)

            output[requirement_id] = EvidenceBundle(
                requirement_id=requirement_id,
                evidence=tuple(items),
                positive_ids=tuple(positive),
                negative_ids=tuple(negative),
                contradictory_ids=tuple(contradictory),
                verified_ids=tuple(verified),
                invalid_ids=tuple(invalid),
            )
        return output
