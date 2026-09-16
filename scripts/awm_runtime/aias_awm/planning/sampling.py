from __future__ import annotations

import math

from aias_awm.planning.models import SamplingPlan


class TemporalSamplingPlanner:
    """Transparent expansion heuristic; not a statistical certification rule."""

    def plan(
        self,
        *,
        case_id: str,
        population_size: int,
        current_sample_size: int,
        high_risk: bool = False,
        recurrence_signal: bool = False,
        stale_periods: list[str] | None = None,
        target_entity_id: str | None = None,
    ) -> SamplingPlan:
        if population_size <= current_sample_size:
            additional = 0
        else:
            base_target = max(3, math.ceil(math.sqrt(population_size)))
            if high_risk:
                base_target = math.ceil(base_target * 1.5)
            if recurrence_signal:
                base_target = math.ceil(base_target * 1.5)
            base_target = min(population_size, base_target)
            additional = max(0, base_target - current_sample_size)

        if recurrence_signal:
            strategy = "RECURRENCE_TARGETED"
        elif stale_periods:
            strategy = "TEMPORAL"
        elif high_risk:
            strategy = "RISK_BASED"
        else:
            strategy = "RISK_BASED"

        return SamplingPlan(
            audit_case_id=case_id,
            target_entity_id=target_entity_id,
            population_size=population_size,
            current_sample_size=current_sample_size,
            additional_sample_size=additional,
            strategy=strategy,
            periods=stale_periods or [],
            rationale=(
                "Deterministic sampling heuristic for evidence acquisition; final sampling sufficiency "
                "remains subject to audit judgement and applicable scheme rules."
            ),
        )
