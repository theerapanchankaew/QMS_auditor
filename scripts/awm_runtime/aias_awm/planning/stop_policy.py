from __future__ import annotations

from aias_awm.planning.models import PlanningContext


class StopEscalatePolicy:
    def decide(self, ctx: PlanningContext, *, admissible_action_count: int) -> tuple[str, str]:
        if ctx.decision_ready:
            return "STOP_DECISION_READY", "World state is decision-ready; hand off to controlled decision kernel."
        if ctx.critical_unknowns and admissible_action_count == 0:
            return "ESCALATE_HUMAN", "Critical uncertainty remains but no admissible evidence-acquisition action is available."
        if ctx.remaining_time_minutes is not None and ctx.remaining_time_minutes <= 0:
            return "STOP_BUDGET", "Audit time budget exhausted before decision sufficiency; escalate unresolved scope."
        return "CONTINUE", "Material uncertainty remains and at least one admissible audit action is available."
