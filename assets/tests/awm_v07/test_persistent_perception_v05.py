from datetime import datetime, timezone
from aias_awm.persistence import Database
from aias_awm.perception.runtime import PersistentPerceptionRuntime
from aias_awm.runtime import AuditWorldRuntime
from aias_awm.adapters.legacy_harness import LegacyAIASHarnessStub
from aias_awm.domain.models import AuditCase
from aias_awm.api.main import create_app
from fastapi.testclient import TestClient


def test_persistent_source_pipeline_and_api(tmp_path):
    db=Database('sqlite+pysqlite:///:memory:'); db.create_schema()
    runtime=AuditWorldRuntime(db, LegacyAIASHarnessStub())
    case=AuditCase(audit_case_id='CASE-P', organization_id='ORG-P', standard_ids=['STD'], audit_type='document_review', scope={}, created_at=datetime.now(timezone.utc))
    runtime.create_case(case)
    p=tmp_path/'pilot.txt'; p.write_text('The pilot had monitoring results but no formal acceptance criteria.', encoding='utf-8')
    pr=PersistentPerceptionRuntime(db)
    result=pr.ingest_file(p, source_id='SRC-P', organization_id='ORG-P', audit_case_id='CASE-P', requirement_id='AR-X', patterns={'AR-X':['acceptance criteria']})
    assert result['span_count'] >= 1 and result['candidate_count'] >= 1
    hits=pr.search('CASE-P','acceptance criteria',top_k=3)
    assert hits and hits[0].source_id=='SRC-P'
    cand=pr.candidates.list_for_case('CASE-P')[0]
    promoted=pr.promote_candidate(cand.candidate_id)
    assert promoted.evidence is not None

    app=create_app(runtime); client=TestClient(app)
    h=client.get('/health'); assert h.status_code==200 and h.json()['version']=='0.7.0'
    rr=client.post('/api/v1/audits/CASE-P/retrieve', json={'query':'acceptance criteria','top_k':3})
    assert rr.status_code==200 and rr.json()['hits']
