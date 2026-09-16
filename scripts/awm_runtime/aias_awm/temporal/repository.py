from __future__ import annotations

from datetime import datetime
from sqlalchemy import insert, select, update, and_, or_

from aias_awm.persistence.database import Database
from aias_awm.persistence.temporal_tables import temporal_facts, corrective_action_links, recurrence_assessments, temporal_drift_events
from .models import TemporalFact, CorrectiveActionLink, RecurrenceAssessment, TemporalDriftEvent


def _upsert(db: Database, table, key_col: str, key_value: str, values: dict) -> None:
    with db.connect() as conn:
        exists = conn.execute(select(table.c[key_col]).where(table.c[key_col] == key_value)).first()
        if exists:
            conn.execute(update(table).where(table.c[key_col] == key_value).values(**values))
        else:
            conn.execute(insert(table).values(**values))


class TemporalFactRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def append(self, fact: TemporalFact) -> None:
        with self.db.connect() as conn:
            if conn.execute(select(temporal_facts.c.fact_id).where(temporal_facts.c.fact_id == fact.fact_id)).first():
                raise ValueError(f"temporal fact already exists: {fact.fact_id}")
            conn.execute(insert(temporal_facts).values(**self._dump(fact)))
            if fact.supersedes_fact_id:
                prior = conn.execute(select(temporal_facts).where(temporal_facts.c.fact_id == fact.supersedes_fact_id)).mappings().first()
                if prior is None:
                    raise ValueError(f"superseded fact not found: {fact.supersedes_fact_id}")
                conn.execute(
                    update(temporal_facts)
                    .where(temporal_facts.c.fact_id == fact.supersedes_fact_id)
                    .values(state="SUPERSEDED")
                )

    def as_of(self, organization_id: str, *, valid_at: datetime, known_at: datetime | None = None,
              entity_ids: list[str] | None = None, fact_types: list[str] | None = None) -> list[TemporalFact]:
        stmt = select(temporal_facts).where(
            temporal_facts.c.organization_id == organization_id,
            temporal_facts.c.valid_from <= valid_at,
            or_(temporal_facts.c.valid_to.is_(None), temporal_facts.c.valid_to > valid_at),
        )
        if known_at is not None:
            stmt = stmt.where(temporal_facts.c.recorded_at <= known_at)
        if entity_ids:
            stmt = stmt.where(temporal_facts.c.entity_id.in_(entity_ids))
        if fact_types:
            stmt = stmt.where(temporal_facts.c.fact_type.in_(fact_types))
        stmt = stmt.order_by(temporal_facts.c.entity_id, temporal_facts.c.fact_type, temporal_facts.c.recorded_at)
        with self.db.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [self._load(dict(r)) for r in rows]

    def current(self, organization_id: str, at: datetime) -> list[TemporalFact]:
        return self.as_of(organization_id, valid_at=at, known_at=at)

    @staticmethod
    def _dump(fact: TemporalFact) -> dict:
        d = fact.model_dump(mode="python")
        d["state"] = fact.state.value
        d["metadata_json"] = d.pop("metadata")
        return d

    @staticmethod
    def _load(d: dict) -> TemporalFact:
        d["metadata"] = d.pop("metadata_json")
        return TemporalFact.model_validate(d)


class CorrectiveActionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
    def upsert(self, item: CorrectiveActionLink) -> None:
        _upsert(self.db, corrective_action_links, "ca_id", item.ca_id, item.model_dump(mode="python"))
    def list_for_requirement(self, organization_id: str, requirement_id: str) -> list[CorrectiveActionLink]:
        with self.db.connect() as conn:
            rows = conn.execute(select(corrective_action_links).where(
                corrective_action_links.c.organization_id == organization_id,
                corrective_action_links.c.requirement_id == requirement_id,
            ).order_by(corrective_action_links.c.raised_at)).mappings().all()
        return [CorrectiveActionLink.model_validate(dict(r)) for r in rows]


class RecurrenceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
    def upsert(self, item: RecurrenceAssessment) -> None:
        _upsert(self.db, recurrence_assessments, "recurrence_id", item.recurrence_id, item.model_dump(mode="python"))
    def list_for_requirement(self, organization_id: str, requirement_id: str) -> list[RecurrenceAssessment]:
        with self.db.connect() as conn:
            rows = conn.execute(select(recurrence_assessments).where(
                recurrence_assessments.c.organization_id == organization_id,
                recurrence_assessments.c.requirement_id == requirement_id,
            ).order_by(recurrence_assessments.c.current_observed_at)).mappings().all()
        return [RecurrenceAssessment.model_validate(dict(r)) for r in rows]


class TemporalDriftRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
    def append(self, item: TemporalDriftEvent) -> None:
        with self.db.connect() as conn:
            conn.execute(insert(temporal_drift_events).values(**item.model_dump(mode="python")))
