from __future__ import annotations

from aias_awm.planning.models import NextActionEvaluation


def evaluate_next_action(case_id: str, predicted: list[str], acceptable_gold: list[str]) -> NextActionEvaluation:
    gold = set(acceptable_gold)
    rank = 0.0
    for idx, action in enumerate(predicted, start=1):
        if action in gold:
            rank = 1.0 / idx
            break
    return NextActionEvaluation(
        case_id=case_id,
        predicted_action_types=predicted,
        acceptable_gold_action_types=acceptable_gold,
        matched=rank > 0.0,
        reciprocal_rank=rank,
    )


def next_action_agreement(items: list[NextActionEvaluation]) -> float:
    if not items:
        return 0.0
    return sum(1 for x in items if x.matched) / len(items)


def mean_reciprocal_rank(items: list[NextActionEvaluation]) -> float:
    if not items:
        return 0.0
    return sum(x.reciprocal_rank for x in items) / len(items)
