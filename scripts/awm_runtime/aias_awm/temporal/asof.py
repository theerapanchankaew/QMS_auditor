from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .models import TemporalFact
from .repository import TemporalFactRepository


class BitemporalQueryService:
    def __init__(self, repository: TemporalFactRepository) -> None:
        self.repository = repository

    def as_of(self, organization_id: str, *, valid_at: datetime, known_at: datetime | None = None,
              entity_ids: list[str] | None = None, fact_types: list[str] | None = None) -> list[TemporalFact]:
        facts = self.repository.as_of(
            organization_id,
            valid_at=valid_at,
            known_at=known_at,
            entity_ids=entity_ids,
            fact_types=fact_types,
        )
        # If multiple transaction-time versions describe the same entity/fact at
        # the same valid time, return the latest one known by known_at.
        latest: dict[tuple[str, str], TemporalFact] = {}
        for fact in facts:
            key = (fact.entity_id, fact.fact_type)
            if key not in latest or fact.recorded_at > latest[key].recorded_at:
                latest[key] = fact
        return sorted(latest.values(), key=lambda x: (x.entity_id, x.fact_type))

    def diff(self, organization_id: str, *, from_valid_at: datetime, to_valid_at: datetime,
             known_at: datetime | None = None) -> dict:
        before = {(f.entity_id, f.fact_type): f for f in self.as_of(
            organization_id, valid_at=from_valid_at, known_at=known_at
        )}
        after = {(f.entity_id, f.fact_type): f for f in self.as_of(
            organization_id, valid_at=to_valid_at, known_at=known_at
        )}
        keys = sorted(set(before) | set(after))
        added, removed, changed = [], [], []
        for key in keys:
            b, a = before.get(key), after.get(key)
            if b is None:
                added.append(a)
            elif a is None:
                removed.append(b)
            elif b.value != a.value or b.fact_id != a.fact_id:
                changed.append({"before": b, "after": a})
        return {"added": added, "removed": removed, "changed": changed}
