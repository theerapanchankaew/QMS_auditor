from __future__ import annotations

from aias_awm.domain.models import AuditAction, AuditHypothesis


_ACTION_BY_MISSING = {
    "effectiveness": "VERIFY_EFFECTIVENESS",
    "approval": "VERIFY_APPROVAL",
    "version": "VERIFY_VERSION",
    "record": "REQUEST_RECORD",
    "document": "REQUEST_DOCUMENT",
    "implementation": "OBSERVE_PROCESS",
    "recurrence": "CHECK_RECURRENCE",
}


class HeuristicAuditPlanner:
    """Deterministic planner for next-best audit actions.

    v0.3 uses transparent heuristics, not reinforcement learning. Priority approximates
    information gain while preserving auditable decision logic.
    """

    def propose(self, hypotheses: list[AuditHypothesis]) -> list[AuditAction]:
        actions: list[AuditAction] = []
        counter = 0
        for h in hypotheses:
            if h.status not in {"UNRESOLVED", "SUPPORTED"}:
                continue
            if not h.unresolved_questions:
                continue
            for q in h.unresolved_questions:
                counter += 1
                ql = q.lower()
                action_type = "REQUEST_RECORD"
                for token, mapped in _ACTION_BY_MISSING.items():
                    if token in ql:
                        action_type = mapped
                        break
                info_gain = 0.95 if "effectiveness" in ql else 0.80
                cost = 0.30 if action_type in {"REQUEST_RECORD", "REQUEST_DOCUMENT"} else 0.50
                priority = round(info_gain / (1.0 + cost), 4)
                actions.append(AuditAction(
                    action_id=f"ACT-{h.audit_case_id}-{counter:03d}",
                    audit_case_id=h.audit_case_id,
                    action_type=action_type,
                    target_requirement_ids=list(h.requirement_ids),
                    rationale=f"Resolve uncertainty: {q}",
                    expected_information_gain=info_gain,
                    cost_score=cost,
                    priority_score=priority,
                    status="PROPOSED",
                ))
        return sorted(actions, key=lambda x: x.priority_score or 0.0, reverse=True)
