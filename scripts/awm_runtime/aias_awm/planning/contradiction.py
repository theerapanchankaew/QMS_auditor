from __future__ import annotations

from aias_awm.domain.models import AuditAction


class ContradictionTargetingPolicy:
    def propose(self, *, case_id: str, requirement_ids: list[str], contradiction_ids: list[str]) -> list[AuditAction]:
        if not contradiction_ids:
            return []
        return [
            AuditAction(
                action_id=f"ACT-{case_id}-CONTRA-001",
                audit_case_id=case_id,
                action_type="CROSS_CHECK",
                target_requirement_ids=requirement_ids,
                rationale=(
                    "Resolve material contradictory evidence before a controlled conclusion: "
                    + ", ".join(contradiction_ids)
                ),
                expected_information_gain=0.96,
                cost_score=0.40,
                priority_score=None,
                status="PROPOSED",
            )
        ]
