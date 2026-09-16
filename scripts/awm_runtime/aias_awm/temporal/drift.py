from __future__ import annotations

from datetime import datetime, timedelta

from .models import TemporalDriftEvent, TemporalFact


class TemporalDriftDetector:
    def detect_stale_world(self, *, organization_id: str, facts: list[TemporalFact], now: datetime,
                           max_age: timedelta) -> list[TemporalDriftEvent]:
        events: list[TemporalDriftEvent] = []
        for fact in facts:
            age = now - fact.recorded_at
            if age > max_age and fact.valid_to is None:
                events.append(TemporalDriftEvent(
                    drift_id=f"DRIFT-{fact.fact_id}",
                    organization_id=organization_id,
                    detected_at=now,
                    drift_type="WORLD_STATE_STALE",
                    severity="WARN",
                    entity_ids=[fact.entity_id],
                    details={"fact_id": fact.fact_id, "age_seconds": age.total_seconds()},
                ))
        return events

    def detect_late_arrival(self, *, organization_id: str, fact: TemporalFact,
                            threshold: timedelta) -> TemporalDriftEvent | None:
        lag = fact.recorded_at - fact.valid_from
        if lag <= threshold:
            return None
        return TemporalDriftEvent(
            drift_id=f"LATE-{fact.fact_id}",
            organization_id=organization_id,
            detected_at=fact.recorded_at,
            drift_type="LATE_ARRIVING_EVIDENCE",
            severity="WARN",
            entity_ids=[fact.entity_id],
            details={"fact_id": fact.fact_id, "lag_seconds": lag.total_seconds()},
        )
