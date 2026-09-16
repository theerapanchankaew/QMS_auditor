from __future__ import annotations

from datetime import datetime, timezone

from aias_awm.cognition.planner import HeuristicAuditPlanner
from aias_awm.domain.models import AuditHypothesis
from aias_awm.planning.contradiction import ContradictionTargetingPolicy
from aias_awm.planning.models import PlannedAction, PlanningContext, PlanningDecision
from aias_awm.planning.scoring import TransparentActionScorer
from aias_awm.planning.stop_policy import StopEscalatePolicy


class AutonomousAuditPlanningPolicy:
    """Controlled next-best-action policy.

    The policy proposes audit actions. It does not execute external actions, alter evidence,
    or release a conformity verdict. Human approval and the existing deterministic decision
    kernel remain authoritative.
    """

    version = "AAP-0.7.0"

    def __init__(self) -> None:
        self.base = HeuristicAuditPlanner()
        self.contradiction = ContradictionTargetingPolicy()
        self.scorer = TransparentActionScorer()
        self.stop = StopEscalatePolicy()

    def plan(self, *, context: PlanningContext, hypotheses: list[AuditHypothesis]) -> PlanningDecision:
        proposed = self.base.propose(hypotheses)
        proposed.extend(self.contradiction.propose(
            case_id=context.audit_case_id,
            requirement_ids=context.unresolved_requirement_ids,
            contradiction_ids=context.contradictory_evidence_ids,
        ))

        # de-duplicate by semantic action/target tuple while preserving first proposal
        deduped = []
        seen = set()
        for action in proposed:
            key = (action.action_type, tuple(sorted(action.target_requirement_ids)), tuple(sorted(action.target_entity_ids)))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(action)

        ranked = [PlannedAction(action=a, score=self.scorer.score(a, context)) for a in deduped]
        ranked.sort(key=lambda x: x.score.utility, reverse=True)
        admissible = [x for x in ranked if x.score.admissible]
        stop_decision, rationale = self.stop.decide(context, admissible_action_count=len(admissible))
        selected = admissible[0].action.action_id if stop_decision == "CONTINUE" and admissible else None
        return PlanningDecision(
            audit_case_id=context.audit_case_id,
            policy_version=self.version,
            ranked_actions=ranked,
            selected_action_id=selected,
            stop_decision=stop_decision,
            rationale=rationale,
            created_at=datetime.now(timezone.utc),
        )
