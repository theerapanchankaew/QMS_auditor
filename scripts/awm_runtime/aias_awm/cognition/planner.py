from __future__ import annotations

from aias_awm.domain.models import AuditAction, AuditHypothesis
from aias_awm.hartley import information_gain_from_resolving_dimension


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

    v0.8: when a hypothesis carries `possible_worlds_dimensions` (populated
    from a clause's assets/requirement_profiles/<clause>.json corpus entry,
    see cognition/hypothesis_engine.py), info_gain is a real, exact
    log2(k)-bit Hartley measure (references/68-hartley-uncertainty.md)
    instead of the hand-picked 0.95/0.80 constant below. Hypotheses without
    dimensions (the common case today -- only clauses whose corpus entry
    has been consumed by a caller carry them) fall back to the original
    heuristic unchanged, so existing behavior and tests are unaffected.
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
                if h.possible_worlds_dimensions and h.requirement_ids and ":" in q:
                    evidence_type = q.split(":", 1)[0].strip()
                    target_dim = f"{h.requirement_ids[0]}_{evidence_type}"
                    ig_result = information_gain_from_resolving_dimension(
                        h.possible_worlds_dimensions, h.known_facts, target_dim,
                    )
                    if ig_result["status"] == "OK":
                        info_gain = ig_result["normalized_information_gain"]
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
