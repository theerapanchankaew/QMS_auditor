from __future__ import annotations

from aias_awm.domain.models import AuditAction
from aias_awm.planning.models import ActionScore, PlanningContext


_DEFAULT_STRENGTH = {
    "REQUEST_DOCUMENT": 0.55,
    "REQUEST_RECORD": 0.80,
    "ASK_INTERVIEW": 0.45,
    "OBSERVE_PROCESS": 0.90,
    "EXPAND_SAMPLE": 0.85,
    "TRACE_TRANSACTION": 0.95,
    "VERIFY_APPROVAL": 0.80,
    "VERIFY_VERSION": 0.75,
    "VERIFY_EFFECTIVENESS": 0.95,
    "CHECK_RECURRENCE": 0.95,
    "CROSS_CHECK": 0.85,
    "ESCALATE_HUMAN": 0.70,
    "STOP": 0.0,
}

_DEFAULT_COST = {
    "REQUEST_DOCUMENT": 0.20,
    "REQUEST_RECORD": 0.25,
    "ASK_INTERVIEW": 0.35,
    "OBSERVE_PROCESS": 0.55,
    "EXPAND_SAMPLE": 0.65,
    "TRACE_TRANSACTION": 0.75,
    "VERIFY_APPROVAL": 0.25,
    "VERIFY_VERSION": 0.20,
    "VERIFY_EFFECTIVENESS": 0.45,
    "CHECK_RECURRENCE": 0.55,
    "CROSS_CHECK": 0.40,
    "ESCALATE_HUMAN": 0.30,
    "STOP": 0.0,
}


class TransparentActionScorer:
    """Auditable heuristic value model.

    It intentionally avoids reinforcement learning in v0.7. All features and weights
    are explicit and versionable so an auditor can reproduce why an action ranked first.
    """

    version = "AAS-0.7.0"

    def score(self, action: AuditAction, ctx: PlanningContext) -> ActionScore:
        coverage = min(1.0, len(action.target_requirement_ids) / max(1, len(ctx.unresolved_requirement_ids)))
        strength = _DEFAULT_STRENGTH[action.action_type]
        cost = action.cost_score if action.cost_score is not None else _DEFAULT_COST[action.action_type]
        info_gain = action.expected_information_gain if action.expected_information_gain is not None else 0.60

        contradiction = 0.0
        if ctx.contradictory_evidence_ids:
            contradiction = 0.95 if action.action_type in {"CROSS_CHECK", "TRACE_TRANSACTION", "OBSERVE_PROCESS"} else 0.30

        temporal = 0.50
        if ctx.stale_evidence_ids:
            temporal = 0.95 if action.action_type in {"VERIFY_VERSION", "EXPAND_SAMPLE", "CHECK_RECURRENCE"} else 0.40

        risk_weight = 1.15 if action.action_type in {"CHECK_RECURRENCE", "TRACE_TRANSACTION", "VERIFY_EFFECTIVENESS"} else 1.0
        numerator = (
            0.32 * info_gain
            + 0.18 * coverage
            + 0.20 * strength
            + 0.15 * contradiction
            + 0.15 * temporal
        ) * risk_weight
        utility = round(numerator / (1.0 + cost), 6)

        admissible = True
        blocked_reason = None
        if ctx.max_action_cost is not None and cost > ctx.max_action_cost:
            admissible = False
            blocked_reason = "ACTION_COST_EXCEEDS_CASE_BUDGET"
        if ctx.remaining_time_minutes is not None and ctx.remaining_time_minutes <= 0:
            admissible = False
            blocked_reason = "NO_REMAINING_AUDIT_TIME"

        return ActionScore(
            action_id=action.action_id,
            information_gain=info_gain,
            requirement_coverage=coverage,
            evidence_strength=strength,
            contradiction_reduction=contradiction,
            temporal_relevance=temporal,
            acquisition_cost=cost,
            risk_weight=risk_weight,
            utility=utility,
            admissible=admissible,
            blocked_reason=blocked_reason,
        )
