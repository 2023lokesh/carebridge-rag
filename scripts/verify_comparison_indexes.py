"""Read-only verification of both real Chroma indexes, exact model budget and IDs."""
import argparse
import json
from pathlib import Path


def verify(db_dir):
    import chromadb
    from sentence_transformers import SentenceTransformer
    root=Path(db_dir)
    meta=json.loads((root/'active_index.json').read_text(encoding='utf8'))
    docs=[json.loads(x) for x in (root/'active_chunks.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
    model=SentenceTransformer(meta['model'])
    client=chromadb.PersistentClient(path=str(root))
    coll=client.get_collection(meta['collection'])
    stored=set(coll.get(include=[])['ids'])
    expected={x['chunk_id'] for x in docs}
    assert len(expected)==len(docs)
    assert stored==expected and coll.count()==len(docs)
    assert all(x['url'].startswith('https://www.cdc.gov/') for x in docs)
    limit=int(model.max_seq_length)
    over=0
    for i in range(0,len(docs),256):
        words=model.tokenizer([x['text'] for x in docs[i:i+256]],truncation=False,
                              padding=False,return_length=True)['length']
        over+=sum(x>limit for x in words)
    assert over==0, f'{over} saved index passages exceed model capacity'
    assert meta['chunks_over_model_limit']==0, 'Build metadata disagrees'
    assert meta['source_urls']>=150 and meta['orphans']==0
    resp=coll.query(query_embeddings=model.encode(['What is the MMR vaccine?'],normalize_embeddings=True).tolist(),
                    n_results=5,include=['metadatas'])
    assert len(resp['ids'][0])==5
    return {'strategy':meta['strategy'],'model':meta['model'],'chunks':len(docs),
            'source_urls':meta['source_urls'],'source_rows':meta['source_rows'],
            'overlong_after':over,'oversized_before':meta['chunks_over_budget_before'],
            'added_windows':meta['chunks_post_budget']-meta['chunks_pre_budget'],
            'orphans':0,'token_limit':limit,
            'p50_model_tokens':meta['p50_model_tokens'],'p95_model_tokens':meta['p95_model_tokens'],
            'max_model_tokens':meta['max_model_tokens'],'top_query_ids':resp['ids'][0],
            'source_corpus_sha256':meta['corpus_sha256']}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--fixed',default='data/chroma_fixed_v2')
    p.add_argument('--heading',default='data/chroma_heading_v2')
    p.add_argument('--output',default='reports/02_chunking_comparison.json')
    a=p.parse_args()
    fixed,heading=verify(a.fixed),verify(a.heading)
    assert fixed['strategy']=='fixed' and heading['strategy']=='heading'
    assert fixed['source_corpus_sha256']==heading['source_corpus_sha256']
    result={'fixed':fixed,'heading':heading,'status':'PASS, tokenizer-safe full index coverage',
            'dev_gold_scored':False,'sealed_test_scored':False}
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
