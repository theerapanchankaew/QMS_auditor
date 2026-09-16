from __future__ import annotations

from dataclasses import dataclass
from .registry import ControlledSourceRegistry
from aias_awm.perception.models import EvidenceCandidate


@dataclass(frozen=True)
class CandidateVerification:
    verified: bool
    failures: tuple[str, ...]


class ProvenanceVerifier:
    def __init__(self, registry: ControlledSourceRegistry):
        self.registry = registry

    def verify_candidate(self, candidate: EvidenceCandidate) -> CandidateVerification:
        failures: list[str] = []
        if not candidate.span_ids:
            failures.append("NO_SOURCE_SPANS")
        for sid in candidate.span_ids:
            result = self.registry.validate_span(sid)
            if not result.ok:
                failures.append(f"{sid}:{result.reason}")
        return CandidateVerification(not failures, tuple(failures))
