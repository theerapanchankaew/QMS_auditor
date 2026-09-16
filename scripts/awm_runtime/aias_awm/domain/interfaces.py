from __future__ import annotations

from typing import Protocol

from .models import AuditAction, AuditHypothesis, AtomicRequirement, EvidenceItem, RequirementAssessment, WorldEvent, WorldSnapshot


class EvidenceExtractor(Protocol):
    def extract(self, source: bytes, context: dict) -> list[EvidenceItem]: ...


class RequirementMapper(Protocol):
    def map(self, evidence: list[EvidenceItem], world: WorldSnapshot) -> list[str]: ...


class EvidenceReconciler(Protocol):
    def reconcile(self, evidence_items: list[EvidenceItem]) -> dict: ...


class RequirementEvaluator(Protocol):
    def assess(self, *, audit_case_id: str, requirement: AtomicRequirement, bundle, applicability: str = "APPLICABLE", now=None) -> RequirementAssessment: ...


class WorldRepository(Protocol):
    def load(self, organization_id: str) -> WorldSnapshot: ...
    def apply(self, event: WorldEvent) -> WorldSnapshot: ...


class HypothesisEngine(Protocol):
    def update(self, case_id: str, assessments: list[RequirementAssessment]) -> list[AuditHypothesis]: ...


class AuditPlanner(Protocol):
    def propose(self, hypotheses: list[AuditHypothesis]) -> list[AuditAction]: ...


class DeterministicHarness(Protocol):
    def enforce(self, candidate: dict, context: dict) -> dict: ...
