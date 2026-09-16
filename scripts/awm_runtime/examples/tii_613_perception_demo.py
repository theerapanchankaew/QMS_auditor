from pathlib import Path
from aias_awm.perception import PerceptionPipeline
from aias_awm.retrieval import HybridRetriever

PDF = Path('/mnt/data/TII_scenario_with_figures(1).pdf')

pipeline = PerceptionPipeline()
result = pipeline.ingest(
    PDF,
    source_id='SRC-TII-CHATBOT-2026',
    organization_id='ORG-TII',
    audit_case_id='CASE-TII-613',
    requirement_id='AR-6.1.3-E06',
    controlled=True,
    version='2026-07-15',
    authority='TII scenario evidence pack',
    patterns={
        'AR-6.1.3-E06': [
            r'acceptance criteria',
            r'เกณฑ์.*ยอมรับ',
            r'effectiveness',
            r'ประสิทธิผล',
            r'12.*error',
            r'12.*ผิด',
        ]
    },
)

print('source_sha256=', result.parse.document.sha256)
print('spans=', len(result.parse.spans))
print('chunks=', len(result.chunks))
print('candidates=', len(result.candidates))
print('manifest_hash=', pipeline.registry.manifest_hash())

retriever = HybridRetriever(result.chunks)
hits = retriever.search('formal acceptance criteria effectiveness evaluation pilot', top_k=5)
for i, hit in enumerate(hits, 1):
    print(f'\nHIT {i} score={hit.score:.4f} chunk={hit.chunk_id}')
    print(hit.text[:900].replace('\n', ' '))

if result.candidates:
    promoted = pipeline.promotion_service().promote_presented(result.candidates[0])
    print('\npromotion=', promoted.reason)
    if promoted.evidence:
        print('epistemic_state=', promoted.evidence.epistemic_state.value)
        print('provenance=', [p.model_dump(mode='json') for p in promoted.evidence.provenance])
