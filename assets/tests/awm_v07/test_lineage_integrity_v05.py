from aias_awm.perception import PerceptionPipeline


def test_hash_lineage_detects_mutation(tmp_path):
    p=tmp_path/'x.txt'; p.write_text('controlled evidence', encoding='utf-8')
    pipe=PerceptionPipeline(); r=pipe.ingest(p, source_id='S', organization_id='O')
    cand=r.candidates[0]
    span=pipe.registry.get_span(cand.span_ids[0])
    # mutate registered text without updating its original hash
    span.text='tampered evidence'
    result=pipe.promotion_service().promote_presented(cand)
    assert result.evidence is None
    assert 'SPAN_HASH_MISMATCH' in result.reason
