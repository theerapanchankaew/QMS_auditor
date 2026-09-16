from __future__ import annotations

from sqlalchemy import delete, insert, select, update

from aias_awm.domain.models import (
    AuditAction,
    AuditCase,
    AuditHypothesis,
    AtomicRequirement,
    EvidenceItem,
    RequirementAssessment,
    WorldEvent,
)
from .database import Database
from .tables import audit_actions, audit_cases, atomic_requirements, evidence_items, hypotheses, requirement_assessments, world_events


def _upsert(db: Database, table, key_col: str, key_value: str, values: dict) -> None:
    with db.connect() as conn:
        exists = conn.execute(select(table.c[key_col]).where(table.c[key_col] == key_value)).first()
        if exists:
            conn.execute(update(table).where(table.c[key_col] == key_value).values(**values))
        else:
            conn.execute(insert(table).values(**values))


class EvidenceRepository:
    def __init__(self, db: Database) -> None: self.db = db
    def upsert(self, item: EvidenceItem) -> None:
        d = item.model_dump(mode="python")
        d["epistemic_state"] = item.epistemic_state.value
        d["provenance"] = [x.model_dump(mode="json") for x in item.provenance]
        d["metadata_json"] = d.pop("metadata")
        _upsert(self.db, evidence_items, "evidence_id", item.evidence_id, d)
    def list_for_case(self, case_id: str) -> list[EvidenceItem]:
        with self.db.connect() as conn:
            rows = conn.execute(select(evidence_items).where(evidence_items.c.audit_case_id == case_id)).mappings().all()
        out=[]
        for r in rows:
            d=dict(r); d["metadata"]=d.pop("metadata_json")
            out.append(EvidenceItem.model_validate(d))
        return out


class RequirementAssessmentRepository:
    def __init__(self, db: Database) -> None: self.db = db
    def upsert(self, item: RequirementAssessment) -> None:
        d=item.model_dump(mode="python"); d["state"]=item.state.value
        _upsert(self.db, requirement_assessments, "assessment_id", item.assessment_id, d)
    def list_for_case(self, case_id: str) -> list[RequirementAssessment]:
        with self.db.connect() as conn:
            rows=conn.execute(select(requirement_assessments).where(requirement_assessments.c.audit_case_id==case_id)).mappings().all()
        return [RequirementAssessment.model_validate(dict(r)) for r in rows]


class HypothesisRepository:
    def __init__(self, db: Database) -> None: self.db=db
    def upsert(self, item: AuditHypothesis) -> None:
        _upsert(self.db, hypotheses, "hypothesis_id", item.hypothesis_id, item.model_dump(mode="python"))
    def list_for_case(self, case_id: str) -> list[AuditHypothesis]:
        with self.db.connect() as conn:
            rows=conn.execute(select(hypotheses).where(hypotheses.c.audit_case_id==case_id)).mappings().all()
        return [AuditHypothesis.model_validate(dict(r)) for r in rows]


class AuditActionRepository:
    def __init__(self, db: Database) -> None: self.db=db
    def upsert(self, item: AuditAction) -> None:
        _upsert(self.db, audit_actions, "action_id", item.action_id, item.model_dump(mode="python"))
    def list_for_case(self, case_id: str) -> list[AuditAction]:
        with self.db.connect() as conn:
            rows=conn.execute(select(audit_actions).where(audit_actions.c.audit_case_id==case_id)).mappings().all()
        return [AuditAction.model_validate(dict(r)) for r in rows]
    def cancel_obsolete(self, case_id: str, active_action_ids: set[str]) -> list[AuditAction]:
        changed: list[AuditAction] = []
        for item in self.list_for_case(case_id):
            if item.status == "PROPOSED" and item.action_id not in active_action_ids:
                item.status = "CANCELLED"
                self.upsert(item)
                changed.append(item)
        return changed


class WorldEventRepository:
    def __init__(self, db: Database) -> None: self.db=db
    def append(self, item: WorldEvent) -> None:
        with self.db.connect() as conn:
            last=conn.execute(select(world_events.c.sequence_no).where(world_events.c.organization_id==item.organization_id).order_by(world_events.c.sequence_no.desc()).limit(1)).scalar_one_or_none()
            expected=0 if last is None else last+1
            if item.sequence_no != expected:
                raise ValueError(f"sequence mismatch: expected {expected}, got {item.sequence_no}")
            conn.execute(insert(world_events).values(**item.model_dump(mode="python")))
    def list(self, organization_id: str, after_seq: int=-1) -> list[WorldEvent]:
        with self.db.connect() as conn:
            rows=conn.execute(select(world_events).where(world_events.c.organization_id==organization_id, world_events.c.sequence_no>after_seq).order_by(world_events.c.sequence_no)).mappings().all()
        return [WorldEvent.model_validate(dict(r)) for r in rows]
    def last_sequence(self, organization_id: str) -> int:
        with self.db.connect() as conn:
            value=conn.execute(select(world_events.c.sequence_no).where(world_events.c.organization_id==organization_id).order_by(world_events.c.sequence_no.desc()).limit(1)).scalar_one_or_none()
        return -1 if value is None else int(value)


class AuditCaseRepository:
    def __init__(self, db: Database) -> None: self.db=db
    def upsert(self, item: AuditCase) -> None:
        _upsert(self.db, audit_cases, "audit_case_id", item.audit_case_id, item.model_dump(mode="python"))
    def get(self, case_id: str) -> AuditCase | None:
        with self.db.connect() as conn:
            row=conn.execute(select(audit_cases).where(audit_cases.c.audit_case_id==case_id)).mappings().first()
        return None if row is None else AuditCase.model_validate(dict(row))


class AtomicRequirementRepository:
    def __init__(self, db: Database) -> None: self.db=db
    def upsert(self, item: AtomicRequirement) -> None:
        d=item.model_dump(mode="python")
        d["object_name"]=d.pop("object")
        d["condition_text"]=d.pop("condition")
        d["evidence_expectations"]=[x.model_dump(mode="json") for x in item.evidence_expectations]
        _upsert(self.db, atomic_requirements, "requirement_id", item.requirement_id, d)
    def get_many(self, requirement_ids: list[str]) -> list[AtomicRequirement]:
        if not requirement_ids: return []
        with self.db.connect() as conn:
            rows=conn.execute(select(atomic_requirements).where(atomic_requirements.c.requirement_id.in_(requirement_ids))).mappings().all()
        out=[]
        for r in rows:
            d=dict(r); d["object"]=d.pop("object_name"); d["condition"]=d.pop("condition_text")
            out.append(AtomicRequirement.model_validate(d))
        return out
