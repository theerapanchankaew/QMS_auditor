from __future__ import annotations

from aias_awm.domain.models import AuditHypothesis, RequirementAssessment, RequirementState


class RuleBasedHypothesisEngine:
    """Produces explicit, inspectable audit hypotheses from requirement states."""

    def update(self, case_id: str, assessments: list[RequirementAssessment]) -> list[AuditHypothesis]:
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
            ))
        return out
