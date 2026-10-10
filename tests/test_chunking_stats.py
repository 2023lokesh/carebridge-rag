from carebridge.index import chunk_stats
from carebridge.corpus import demo_documents,chunk_documents

def test_two_chunk_strategy_distributions_and_manifest():
    docs=demo_documents()
    fixed=chunk_documents(docs,'fixed')
    heading=chunk_documents(docs,'heading')
    assert fixed and heading
    assert not {d['chunk_id'] for d in fixed}&{d['chunk_id'] for d in heading}
    for chunks in [fixed,heading]:
        res=chunk_stats(chunks)
        assert res['chunks']==len(chunks) and res['p95_words']>0
