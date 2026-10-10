"""Real, *retrieval-only* B1/B2/B3 development evaluation; never reads sealed test.

B1: exact BM25 on fixed, tokenizer-capped chunks.
B2: Chroma MiniLM cosine on same fixed chunks.
B3: BM25+dense RRF on heading chunks, cross-encoder re-ranks 20 down to top 5.
The gold file stays local. Produces no personal question text in output.
"""
import argparse
import json
import math
import statistics
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path
from carebridge.corpus import tokenize


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf8').splitlines() if line.strip()]


def bm25_rank(query, docs, limit=20):
    """Reproducible Okapi BM25 ranking (k1=1.2, b=0.75); no TF-IDF postscore."""
    tokens = [tokenize(d.get('title','')+' '+d.get('section','')+' '+d['text']) for d in docs]
    df=Counter(t for toks in tokens for t in set(toks))
    avg=sum(len(t) for t in tokens)/max(1,len(tokens))
    terms=set(tokenize(query)); n=len(tokens)
    scored=[]
    for i,ts in enumerate(tokens):
        counts=Counter(ts)
        weight=1.2*(.25+.75*len(ts)/max(1,avg))
        score=sum(math.log(1+(n-df[t]+.5)/(df[t]+.5))*counts[t]*2.2/(counts[t]+weight)
                  for t in terms if counts[t])
        scored.append((i,score))
    return [i for i,_ in sorted(scored,key=lambda x:(-x[1],x[0]))[:limit]]


def _metrics(gold_urls, ranked_docs, candidate_pool=None):
    """URL-labelled retrieval proxies, de-duplicate relevant URL credit."""
    gold=set(gold_urls); found=set(); positions=[]
    for rank,d in enumerate(ranked_docs,1):
        url=d.get('url',d.get('source_url'))
        if url in gold and url not in found:
            found.add(url)
            positions.append(rank)
    best=min(len(gold),10)
    idcg=sum(1/math.log2(i+1) for i in range(1,best+1)) if best else 1
    return {'recall_at_5':sum(i<=5 for i in positions)/len(gold),
            'recall_at_20':sum(i<=20 for i in positions)/len(gold),
            'mrr':1/min(positions) if positions else 0,
            'ndcg_at_10':sum(1/math.log2(i+1) for i in positions if i<=10)/idcg}


def bootstrap_paired(a,b,metric='recall_at_5',seed=633,n=2000):
    import random
    ids=sorted(set(a)&set(b))
    if not ids:return None
    changes=[b[i][metric]-a[i][metric] for i in ids]
    rng=random.Random(seed); k=len(changes)
    samples=sorted(sum(changes[rng.randrange(k)] for _ in range(k))/k for _ in range(n))
    return {'metric':metric,'questions':k,'mean_delta':round(sum(changes)/k,4),
            'bootstrap_95_ci':[round(samples[int(.025*(n-1))],4),round(samples[int(.975*(n-1))],4)]}


def _load_neural(db_dir):
    import chromadb
    from sentence_transformers import SentenceTransformer
    root=Path(db_dir)
    meta=json.loads((root/'active_index.json').read_text())
    docs=read_jsonl(root/'active_chunks.jsonl')
    coll=chromadb.PersistentClient(path=str(root)).get_collection(meta['collection'])
    assert coll.count()==len(docs) and len({d['chunk_id'] for d in docs})==len(docs)
    model=SentenceTransformer(meta['model'])
    return meta,docs,coll,model


def _dense_ranks(question,docs,collection,model,k=20):
    if not docs:return []
    emb=model.encode([question],normalize_embeddings=True).tolist()
    matches=collection.query(query_embeddings=emb,n_results=min(k,len(docs)))['ids'][0]
    lookup={x['chunk_id']:i for i,x in enumerate(docs)}
    return [lookup[m] for m in matches]


def _eval_gold(dev_path):
    gold=read_jsonl(dev_path)
    if len(gold)!=24 or len({x['id'] for x in gold})!=24 or any(x.get('split')!='dev' for x in gold):
        raise ValueError('Refusing non-frozen development set: exactly 24 DEV rows required')
    if any(x.get('review_status')!='HUMAN_VERIFIED' for x in gold):
        raise ValueError('Gold rows lack human review attestation')
    # Unanswerable and ambiguous-without-references must be evaluated for refusal separately.
    return [x for x in gold if x.get('gold_source_urls')]


def evaluate(baseline, dev_path, db_dir, output):
    gold=_eval_gold(dev_path)
    meta,docs,coll,model=None,None,None,None
    if baseline in ('B2','B3'):
        meta,docs,coll,model=_load_neural(db_dir)
        expected='fixed' if baseline=='B2' else 'heading'
        if meta['strategy']!=expected:raise ValueError(f'{baseline} needs {expected} index')
    else:
        docs=read_jsonl(Path(db_dir)/'active_chunks.jsonl')
        meta=json.loads((Path(db_dir)/'active_index.json').read_text())
        if meta['strategy']!='fixed':raise ValueError('B1 needs fixed index')
    cross_encoder=None
    if baseline=='B3':
        from sentence_transformers import CrossEncoder
        cross_encoder=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    results=[]
    for row in gold:
        query=row['question']; start=time.perf_counter()
        pre_rerank_metrics=None
        if baseline=='B1':
            ranks=bm25_rank(query,docs,20)
        elif baseline=='B2':
            ranks=_dense_ranks(query,docs,coll,model,20)
        else:
            bm=bm25_rank(query,docs,20)
            dense=_dense_ranks(query,docs,coll,model,20)
            bmr={ix:rank for rank,ix in enumerate(bm,1)}
            dr={ix:rank for rank,ix in enumerate(dense,1)}
            candidates=set(bm)|set(dense)
            ranks=sorted(candidates,key=lambda ix:-(1/(60+bmr[ix]) if ix in bmr else 0)-
                         (1/(60+dr[ix]) if ix in dr else 0))[:20]
            pre_rerank_metrics=_metrics(row['gold_source_urls'],[docs[i] for i in ranks])
            scores=cross_encoder.predict([[query,docs[i]['text']] for i in ranks])
            ranks=[ix for ix,_ in sorted(zip(ranks,scores),key=lambda e:float(e[1]),reverse=True)]
        latency=(time.perf_counter()-start)*1000
        m=_metrics(row['gold_source_urls'],[docs[i] for i in ranks])
        results.append({'id':row['id'],'category':row['category'],'metrics':m,
                        'latency_ms':round(latency,2), 'candidate_chunks':len(ranks),
                        'top_5_chunk_ids':[docs[i]['chunk_id'] for i in ranks[:5]],
                        'top_20_urls':[docs[i]['url'] for i in ranks],
                        **({'pre_rerank_metrics':pre_rerank_metrics} if pre_rerank_metrics is not None else {})})
    latencies=sorted(x['latency_ms'] for x in results)
    summary={'baseline':baseline,'index_strategy':meta['strategy'],'index_model':meta['model'],
             'source_pages':meta.get('source_urls'),'indexed_chunks':len(docs),
             'development_questions':24,'source_labelled_questions':len(gold),
             'unanswerable_and_unscorable_excluded':24-len(gold),
             'metrics_scope':'source-URL-labelled retrieval ONLY, no answer correctness/abstention scoring',
             'reranker':'cross-encoder/ms-marco-MiniLM-L-6-v2' if baseline=='B3' else 'none',
             'p50_retrieval_ms':round(statistics.median(latencies),2),
             'p95_retrieval_ms':round(latencies[min(len(latencies)-1,math.ceil(len(latencies)*.95)-1)],2)}
    for key in ['recall_at_5','recall_at_20','mrr','ndcg_at_10']:
        summary[key]=round(statistics.mean(row['metrics'][key] for row in results),4)
    outcome={'summary':summary,'per_question':results}
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError(f'Do not overwrite prior evaluation {dest}')
    dest.write_text(json.dumps(outcome,indent=2)+'\n',encoding='utf8')
    return outcome


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True,choices=['B1','B2','B3'])
    p.add_argument('--dev',required=True,help='PRIVATE 24-item frozen dev JSONL; never upload test questions')
    p.add_argument('--db-dir',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    print(json.dumps(evaluate(a.baseline,a.dev,a.db_dir,a.output)['summary'],indent=2))

if __name__=='__main__':main()
