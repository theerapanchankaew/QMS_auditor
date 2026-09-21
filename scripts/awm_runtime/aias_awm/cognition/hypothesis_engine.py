from __future__ import annotations

from aias_awm.domain.models import AuditHypothesis, RequirementAssessment, RequirementState


class RuleBasedHypothesisEngine:
    """Produces explicit, inspectable audit hypotheses from requirement states."""

    def update(
        self,
        case_id: str,
        assessments: list[RequirementAssessment],
        dimensions_by_requirement: dict[str, dict[str, list[str]]] | None = None,
    ) -> list[AuditHypothesis]:
        """dimensions_by_requirement is optional and defaults to None for full
        backward compatibility with existing callers. When supplied (keyed by
        requirement_id, e.g. loaded from a clause's
        assets/requirement_profiles/<clause>.json possible_worlds_dimensions
        block), the resulting hypothesis carries the real Hartley dimension
        set so scripts/awm_runtime's planner can compute an exact
        log2(k)-bit information gain instead of its hand-picked heuristic
        constant -- see cognition/planner.py and
        references/68-hartley-uncertainty.md. known_facts is left empty here
        (no evidence-to-dimension mapping exists yet); it is the caller's
        responsibility to update it as evidence is confirmed."""
        dimensions_by_requirement = dimensions_by_requirement or {}
        out: list[AuditHypothesis] = []
        for index, a in enumerate(assessments, start=1):
            hid = f"HYP-{case_id}-{index:03d}"
            if a.state == RequirementState.BREACH_PROVEN:
                htype, status = "BREACH", "SUPPORTED"
                statement = f"Requirement {a.requirement_id} is not fulfilled based on explicit evidence."
                questions = []
            elif a.state in {RequirementState.INSUFFICIENT_EVIDENCE, RequirementState.PARTIALLY_SUPPORTED}:
                htype, status = "INSUFFICIENT_EVIDENCE", "SUPPORTED"
                statement = f"Requirement {a.requirement_id} cannot yet be concluded because decision-critical evidence is missing."
                questions = list(a.missing_evidence)
            elif a.state == RequirementState.CONTRADICTORY:
                htype, status = "INSUFFICIENT_EVIDENCE", "UNRESOLVED"
                statement = f"Requirement {a.requirement_id} has conflicting evidence that requires reconciliation."
                questions = ["resolve conflicting evidence"]
            elif a.state == RequirementState.SATISFIED:
                htype, status = "CONFORMITY", "SUPPORTED"
                statement = f"Requirement {a.requirement_id} is supported by the current evidence set."
                questions = []
            else:
                htype, status = "INSUFFICIENT_EVIDENCE", "UNRESOLVED"
                statement = f"Requirement {a.requirement_id} remains unresolved."
                questions = list(a.missing_evidence)

            out.append(AuditHypothesis(
                hypothesis_id=hid,
                audit_case_id=case_id,
                hypothesis_type=htype,
                statement=statement,
                requirement_ids=[a.requirement_id],
                supporting_evidence_ids=list(a.positive_evidence_ids),
                contradicting_evidence_ids=list(a.contradictory_evidence_ids),
                status=status,
                unresolved_questions=questions,
                possible_worlds_dimensions=dimensions_by_requirement.get(a.requirement_id),
            ))
        return out
