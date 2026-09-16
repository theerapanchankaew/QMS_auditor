from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aias_awm.domain.models import AtomicRequirement, EvidenceItem, RequirementAssessment, AuditHypothesis, AuditAction
from .evidence_reconciliation import EvidenceReconciliationEngine
from .requirement_engine import RequirementStateEngine
from .hypothesis_engine import RuleBasedHypothesisEngine
from .planner import HeuristicAuditPlanner


@dataclass(frozen=True)
class CognitionResult:
    assessments: tuple[RequirementAssessment, ...]
    hypotheses: tuple[AuditHypothesis, ...]
    actions: tuple[AuditAction, ...]
    decision_ready: bool


class AuditCognitionPipeline:
    def __init__(self) -> None:
        self.reconciler = EvidenceReconciliationEngine()
        self.requirements = RequirementStateEngine()
        self.hypotheses = RuleBasedHypothesisEngine()
        self.planner = HeuristicAuditPlanner()

    def run(
        self,
        *,
        audit_case_id: str,
        atomic_requirements: list[AtomicRequirement],
        evidence_items: list[EvidenceItem],
        now: datetime | None = None,
    ) -> CognitionResult:
        bundles = self.reconciler.reconcile(evidence_items)
        assessments = [
            self.requirements.assess(
                audit_case_id=audit_case_id,
                requirement=req,
                bundle=bundles.get(req.requirement_id),
                now=now,
            )
            for req in atomic_requirements
        ]
        hypotheses = self.hypotheses.update(audit_case_id, assessments)
        actions = self.planner.propose(hypotheses)
        decision_ready = all(a.state.value in {"SATISFIED", "BREACH_PROVEN", "NOT_APPLICABLE"} for a in assessments)
        return CognitionResult(tuple(assessments), tuple(hypotheses), tuple(actions), decision_ready)
