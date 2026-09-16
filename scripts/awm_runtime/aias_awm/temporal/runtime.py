from __future__ import annotations
from datetime import datetime, timedelta

from aias_awm.persistence.database import Database
from .models import TemporalFact, CorrectiveActionLink
from .repository import TemporalFactRepository, CorrectiveActionRepository, RecurrenceRepository, TemporalDriftRepository
from .asof import BitemporalQueryService
from .recurrence import RecurrenceEngine
from .drift import TemporalDriftDetector

class TemporalAuditRuntime:
    def __init__(self, db: Database) -> None:
        self.db=db; self.facts=TemporalFactRepository(db); self.cas=CorrectiveActionRepository(db)
        self.recurrences=RecurrenceRepository(db); self.drifts=TemporalDriftRepository(db)
        self.query=BitemporalQueryService(self.facts); self.recurrence_engine=RecurrenceEngine(); self.drift_detector=TemporalDriftDetector()

    def record_fact(self, fact: TemporalFact) -> TemporalFact:
        self.facts.append(fact); return fact

    def as_of(self, organization_id: str, *, valid_at: datetime, known_at: datetime|None=None):
        return self.query.as_of(organization_id, valid_at=valid_at, known_at=known_at)

    def assess_recurrence(self, **kwargs):
        item=self.recurrence_engine.assess(**kwargs); self.recurrences.upsert(item); return item
