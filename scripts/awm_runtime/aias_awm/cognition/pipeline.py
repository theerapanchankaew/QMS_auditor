from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aias_awm.domain.models import AtomicRequirement, EvidenceItem, RequirementAssessment, AuditHypothesis, AuditAction
from .evidence_reconciliation import EvidenceReconciliationEngine
from .requirement_engine import RequirementStateEngine
from .hypothesis_engine import RuleBasedHypothesisEngine
from .planner import HeuristicAuditPlanner
from aias_awm.qualifiers import FAMILY_B, family_of, l7_inputs, phrases_in


def _applicability_for(requirement: AtomicRequirement, bundle) -> str:
    """L7 (references/26 § L7): a not-applicable determination the organization
    recorded as evidence (metadata org_determination="not_applicable", see
    aias_awm/qualifiers.py) is passed to the assessment as NOT_APPLICABLE so the
    element is decision-ready; the L7 gate / harness then decide the verdict.
    Never for 'as appropriate' (Annex A.2(a)) and never when objective evidence
    shows the condition applies or the determinations conflict."""
    phrases = phrases_in(requirement.qualifier)
    if not phrases or any(family_of(p) == FAMILY_B for p in phrases):
        return "APPLICABLE"
    inputs = l7_inputs(list(bundle.evidence) if bundle else [], "APPLICABLE")
    if inputs["determination"] == "not_applicable" and not inputs["condition_evidenced"] and not inputs["determination_conflict"]:
        return "NOT_APPLICABLE"
    return "APPLICABLE"


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
        dimensions_by_requirement: dict[str, dict[str, list[str]]] | None = None,
    ) -> CognitionResult:
        """dimensions_by_requirement is optional and defaults to None for full
        backward compatibility. When supplied (keyed by requirement_id), it is
        passed straight through to the hypothesis engine so the resulting
        hypotheses -- and, downstream, the planner's info_gain -- use a real
        Hartley measure instead of the fallback heuristic constant. See
        cognition/hypothesis_engine.py, cognition/planner.py, and
        references/68-hartley-uncertainty.md. This package does not load
        assets/requirement_profiles/ itself (it stays independently
        installable -- see aias_awm/hartley.py's own docstring); the caller
        is responsible for loading that corpus and building this dict."""
        bundles = self.reconciler.reconcile(evidence_items)
        assessments = [
            self.requirements.assess(
                audit_case_id=audit_case_id,
                requirement=req,
                bundle=bundles.get(req.requirement_id),
                applicability=_applicability_for(req, bundles.get(req.requirement_id)),
                now=now,
            )
            for req in atomic_requirements
        ]
        hypotheses = self.hypotheses.update(audit_case_id, assessments, dimensions_by_requirement)
        actions = self.planner.propose(hypotheses)
        decision_ready = all(a.state.value in {"SATISFIED", "BREACH_PROVEN", "NOT_APPLICABLE"} for a in assessments)
        return CognitionResult(tuple(assessments), tuple(hypotheses), tuple(actions), decision_ready)
