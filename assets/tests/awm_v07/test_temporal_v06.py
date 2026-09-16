from datetime import datetime, timezone, timedelta
from aias_awm.persistence.database import Database
from aias_awm.temporal import TemporalFact, TemporalFactRepository, BitemporalQueryService, CorrectiveActionLink, RecurrenceEngine, TemporalDriftDetector

UTC=timezone.utc

def db():
    d=Database('sqlite+pysqlite:///:memory:'); d.create_schema(); return d

def test_bitemporal_as_of_latest_known_version():
    d=db(); r=TemporalFactRepository(d); q=BitemporalQueryService(r)
    r.append(TemporalFact(fact_id='F1',organization_id='O1',entity_id='P1',fact_type='status',value={'v':'old'},valid_from=datetime(2026,1,1,tzinfo=UTC),valid_to=None,recorded_at=datetime(2026,1,2,tzinfo=UTC)))
    r.append(TemporalFact(fact_id='F2',organization_id='O1',entity_id='P1',fact_type='status',value={'v':'corrected'},valid_from=datetime(2026,1,1,tzinfo=UTC),valid_to=None,recorded_at=datetime(2026,2,1,tzinfo=UTC),supersedes_fact_id='F1'))
    early=q.as_of('O1',valid_at=datetime(2026,1,15,tzinfo=UTC),known_at=datetime(2026,1,20,tzinfo=UTC))
    late=q.as_of('O1',valid_at=datetime(2026,1,15,tzinfo=UTC),known_at=datetime(2026,2,2,tzinfo=UTC))
    assert early[0].value['v']=='old'
    assert late[0].value['v']=='corrected'

def test_recurrence_not_m5_without_verified_effectiveness():
    ca=CorrectiveActionLink(ca_id='CA1',organization_id='O1',finding_id='NC1',requirement_id='R1',raised_at=datetime(2026,1,1,tzinfo=UTC),effectiveness_result='NOT_VERIFIED')
    x=RecurrenceEngine().assess(recurrence_id='REC1',organization_id='O1',requirement_id='R1',prior_finding_id='NC1',current_finding_id='NC2',current_observed_at=datetime(2026,6,1,tzinfo=UTC),prior_ca=ca,same_or_equivalent_failure=True,representative_scope_confirmed=True,evidence_ids=['E2'])
    assert not x.recurrence_proven and not x.m5_eligible

def test_recurrence_m5_signal_after_effective_closure():
    ca=CorrectiveActionLink(ca_id='CA1',organization_id='O1',finding_id='NC1',requirement_id='R1',raised_at=datetime(2026,1,1,tzinfo=UTC),effectiveness_verified_at=datetime(2026,3,1,tzinfo=UTC),effectiveness_result='EFFECTIVE')
    x=RecurrenceEngine().assess(recurrence_id='REC1',organization_id='O1',requirement_id='R1',prior_finding_id='NC1',current_finding_id='NC2',current_observed_at=datetime(2026,6,1,tzinfo=UTC),prior_ca=ca,same_or_equivalent_failure=True,representative_scope_confirmed=True,evidence_ids=['E2'])
    assert x.recurrence_proven and x.m5_eligible

def test_late_arriving_evidence_drift():
    f=TemporalFact(fact_id='F1',organization_id='O1',entity_id='P1',fact_type='kpi',value={'x':1},valid_from=datetime(2026,1,1,tzinfo=UTC),recorded_at=datetime(2026,1,20,tzinfo=UTC))
    evt=TemporalDriftDetector().detect_late_arrival(organization_id='O1',fact=f,threshold=timedelta(days=7))
    assert evt is not None and evt.drift_type=='LATE_ARRIVING_EVIDENCE'
