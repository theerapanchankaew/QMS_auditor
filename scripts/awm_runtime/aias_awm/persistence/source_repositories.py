from __future__ import annotations

from sqlalchemy import insert, select, update
from aias_awm.perception.models import SourceDocument, SourceSpan, DocumentChunk, EvidenceCandidate
from .database import Database
from .source_tables import source_documents, source_spans, document_chunks, evidence_candidates


def _upsert(db, table, key, value, values):
    with db.connect() as conn:
        exists = conn.execute(select(table.c[key]).where(table.c[key] == value)).first()
        if exists:
            conn.execute(update(table).where(table.c[key] == value).values(**values))
        else:
            conn.execute(insert(table).values(**values))


class SourceDocumentRepository:
    def __init__(self, db: Database): self.db = db
    def upsert(self, item: SourceDocument):
        d = item.model_dump(mode="python"); d["kind"] = item.kind.value; d["metadata_json"] = d.pop("metadata")
        _upsert(self.db, source_documents, "source_id", item.source_id, d)
    def get(self, source_id: str):
        with self.db.connect() as conn:
            row = conn.execute(select(source_documents).where(source_documents.c.source_id == source_id)).mappings().first()
        if not row: return None
        d = dict(row); d["metadata"] = d.pop("metadata_json")
        return SourceDocument.model_validate(d)
    def list_for_case(self, case_id: str):
        with self.db.connect() as conn:
            rows = conn.execute(select(source_documents).where(source_documents.c.audit_case_id == case_id)).mappings().all()
        out=[]
        for row in rows:
            d=dict(row); d["metadata"]=d.pop("metadata_json"); out.append(SourceDocument.model_validate(d))
        return out


class SourceSpanRepository:
    def __init__(self, db: Database): self.db = db
    def upsert_many(self, items: list[SourceSpan]):
        for item in items:
            d=item.model_dump(mode="python"); d["metadata_json"] = d.pop("metadata")
            _upsert(self.db, source_spans, "span_id", item.span_id, d)
    def list_for_source(self, source_id: str):
        with self.db.connect() as conn:
            rows=conn.execute(select(source_spans).where(source_spans.c.source_id==source_id)).mappings().all()
        out=[]
        for row in rows:
            d=dict(row); d["metadata"]=d.pop("metadata_json"); out.append(SourceSpan.model_validate(d))
        return out
    def get(self, span_id: str):
        with self.db.connect() as conn:
            row=conn.execute(select(source_spans).where(source_spans.c.span_id==span_id)).mappings().first()
        if not row: return None
        d=dict(row); d["metadata"]=d.pop("metadata_json"); return SourceSpan.model_validate(d)


class DocumentChunkRepository:
    def __init__(self, db: Database): self.db=db
    def upsert_many(self, items: list[DocumentChunk]):
        for item in items:
            d=item.model_dump(mode="python"); d["metadata_json"] = d.pop("metadata")
            _upsert(self.db, document_chunks, "chunk_id", item.chunk_id, d)
    def list_for_case(self, case_id: str):
        with self.db.connect() as conn:
            rows=conn.execute(select(document_chunks).select_from(document_chunks.join(source_documents, document_chunks.c.source_id==source_documents.c.source_id)).where(source_documents.c.audit_case_id==case_id)).mappings().all()
        out=[]
        for row in rows:
            d={k:row[k] for k in document_chunks.c.keys()}; d["metadata"]=d.pop("metadata_json"); out.append(DocumentChunk.model_validate(d))
        return out
    def list_for_source(self, source_id: str):
        with self.db.connect() as conn:
            rows=conn.execute(select(document_chunks).where(document_chunks.c.source_id==source_id).order_by(document_chunks.c.ordinal)).mappings().all()
        out=[]
        for row in rows:
            d=dict(row); d["metadata"]=d.pop("metadata_json"); out.append(DocumentChunk.model_validate(d))
        return out


class EvidenceCandidateRepository:
    def __init__(self, db: Database): self.db=db
    def upsert_many(self, items: list[EvidenceCandidate]):
        for item in items: self.upsert(item)
    def upsert(self, item: EvidenceCandidate):
        d=item.model_dump(mode="python"); d["candidate_state"] = item.candidate_state.value; d["metadata_json"] = d.pop("metadata")
        _upsert(self.db, evidence_candidates, "candidate_id", item.candidate_id, d)
    def get(self, candidate_id: str):
        with self.db.connect() as conn:
            row=conn.execute(select(evidence_candidates).where(evidence_candidates.c.candidate_id==candidate_id)).mappings().first()
        if not row: return None
        d=dict(row); d["metadata"]=d.pop("metadata_json"); return EvidenceCandidate.model_validate(d)
    def list_for_case(self, case_id: str):
        with self.db.connect() as conn:
            rows=conn.execute(select(evidence_candidates).where(evidence_candidates.c.audit_case_id==case_id)).mappings().all()
        out=[]
        for row in rows:
            d=dict(row); d["metadata"]=d.pop("metadata_json"); out.append(EvidenceCandidate.model_validate(d))
        return out
