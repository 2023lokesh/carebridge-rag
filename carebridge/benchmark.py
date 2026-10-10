"""Graded evaluation gate. Only human-confirmed labels, real corpus, and real models.

Never substitute TF-IDF for neural dense B2 or a proxy re-score for B3.
Never run an untouched test split a second time.
"""
import argparse
import hashlib
import json
import math
import os
import statistics
import time
from pathlib import Path
from .evaluate import stratified_split
from .audit import audit

BASELINES={
    'B0':'Closed-book LLM with no retrieval (requires human-assessed answers)',
    'B1':'BM25 retrieval on fixed chunks + same generator',
    'B2':'Neural dense retrieval on fixed chunks + same generator',
    'B3':'Heading-aware chunks, BM25/neural RRF, cross-encoder reranker, same generator',
}

def verify_item(row):
    id_=row.get('id','unknown')
    if row.get('review_status')!='HUMAN_VERIFIED' or not row.get('human_verified_by'):
        raise ValueError(f'{id_}: only independently HUMAN_VERIFIED records may be used as graded gold')
    if not row.get('human_verified_at'):
        raise ValueError(f'{id_}: missing verification timestamp')
    if row['category'] not in {'unanswerable','ambiguous_adversarial'}:
        if not row.get('gold_source_urls') or not row.get('gold_answer'):
            raise ValueError(f'{id_}: a gold answer and source URL(s) are required')
        quote=row.get('evidence_quote') or ''
        if not quote or len(quote.split())>25:
            raise ValueError(f'{id_}: human must record an evidence quote of <=25 words')
    if row['category']=='unanswerable' and not row.get('searches_performed'):
        raise ValueError(f'{id_}: record how absence was independently checked')

def check_ready(items,manifest,normalized):
    for row in items:verify_item(row)
    corpus=audit(manifest,normalized)
    if not corpus['meets_assignment_minima']:
        raise ValueError(f'No graded benchmark: corpus minima unmet: {corpus}')
    dev,test=stratified_split(items)
    return dev,test,corpus

def metric_per_question(gold_urls, retrieved):
    urls=set(gold_urls)
    ranks=[i for i,d in enumerate(retrieved,1) if d.get('url',d.get('source_url')) in urls]
    # Page-level labels are less strict than manually mapped chunk relevance.
    dcg=sum(1/math.log2(i+1) for i in ranks if i<=10)
    best=min(len(urls),10)
    idcg=sum(1/math.log2(i+1) for i in range(1,best+1)) if best else 0
    return {'recall_at_5':len([x for x in ranks if x<=5])/len(urls) if urls else None,
            'recall_at_20':len([x for x in ranks if x<=20])/len(urls) if urls else None,
            'mrr':1/min(ranks) if ranks else 0., 'ndcg_at_10':dcg/idcg if idcg else None}

def bootstrap_ci(deltas,repetitions=2000,seed=633):
    import random
    if not deltas:return None
    rand=random.Random(seed);n=len(deltas)
    means=sorted(sum(deltas[rand.randrange(n)] for _ in range(n))/n for _ in range(repetitions))
    return {'mean_delta':round(sum(deltas)/n,5), 'bootstrap_95_ci':[round(means[int(.025*(repetitions-1))],5),round(means[int(.975*(repetitions-1))],5)]}

def run(args):
    if args.split=='test' and not args.confirm_test_once:
        raise ValueError('TEST SET MUST NOT RUN WITHOUT explicit --confirm-test-once')
    if args.baseline=='B0' and not os.environ.get('OPENAI_API_KEY'):
        raise ValueError('B0 requires a real configured language model; cannot substitute a scripted refusal')
    if args.baseline in {'B2','B3'}:
        try:import chromadb,sentence_transformers
        except ImportError as exc:
            raise ValueError('B2/B3 require installed neural model and Chroma dependencies') from exc
        pointer=Path('data/chroma/active_index.json')
        if not pointer.exists():
            raise ValueError('B2/B3 require previously built real Chroma index')
        actual=json.loads(pointer.read_text())['strategy']
        needed='fixed' if args.baseline=='B2' else 'heading'
        if actual!=needed:
            raise ValueError(f'Wrong active chunk strategy for {args.baseline}: index={actual}, needed={needed}; rebuild from normalized corpus first')
    items=[json.loads(x) for x in Path(args.gold).read_text().splitlines() if x.strip()]
    dev,test,inventory=check_ready(items,args.manifest,args.normalized)
    chosen=dev if args.split=='dev' else test
    fingerprint=hashlib.sha256(Path(args.gold).read_bytes()).hexdigest()[:16]
    outfile=Path(args.output)
    # Test lock applies across baselines; use unique baseline paths but one shared test lock.
    lock=Path('data/evaluation-test-once.lock')
    if args.split=='test' and lock.exists():
        raise ValueError('Holdout test already run according to test-once lock; do not peek/re-run')
    if outfile.exists():raise FileExistsError(f'Refusing to overwrite a benchmark: {outfile}')
    # This script computes retrieval-only metrics. Grounded answer correctness,
    # citation validity, and B0 closed-book must be scored separately by humans.
    if args.baseline=='B0':
        raise ValueError('B0 generation scoring requires a separately approved LLM/answer-evaluation protocol; no bogus B0 number emitted.')
    if args.baseline=='B1':
        from .rag import retrieve
        def fn(q):return retrieve(q,'bm25',20,args.normalized)
    else:
        from .full_backend import retrieve_full
        def fn(q):return retrieve_full(q,'dense' if args.baseline=='B2' else 'hybrid',20,rerank=args.baseline=='B3')
    rows=[]
    for item in chosen:
        started=time.perf_counter();retrieved,stats=fn(item['question']);elapsed=(time.perf_counter()-started)*1000
        if item['category']=='unanswerable':continue
        metrics=metric_per_question(item['gold_source_urls'],retrieved)
        rows.append({'id':item['id'],'metrics':metrics,'latency_ms':round(elapsed,2),'candidate_pool':len(retrieved),'ranked_ids':[r['chunk_id'] for r in retrieved]})
    summary={'description':BASELINES[args.baseline],'baseline':args.baseline,'split':args.split,
             'gold_sha256_16':fingerprint,'full_gold_items':len(items),'evaluated_answerable':len(rows),
             'corpus':{key:inventory[key] for key in ('unique_pages','pdf_documents','html_table_pages')},
             'retrieval_only':True,'answer_correctness':'NOT SCORED','citation_validity':'NOT SCORED',
             'refusal_rates':'NOT SCORED','cost_per_query':'NOT SCORED',
             'p50_retrieval_ms':round(statistics.median(r['latency_ms'] for r in rows),3) if rows else None,
             'p95_retrieval_ms':round(sorted(r['latency_ms'] for r in rows)[min(len(rows)-1,math.ceil(len(rows)*.95)-1)],3) if rows else None}
    for m in ['recall_at_5','recall_at_20','mrr','ndcg_at_10']:
        arr=[r['metrics'][m] for r in rows if r['metrics'][m] is not None]
        summary[m]=round(statistics.mean(arr),4) if arr else None
    outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps({'summary':summary,'item_results':rows},indent=2))
    if args.split=='test':lock.write_text(json.dumps({'gold_sha256_16':fingerprint,'started_by':args.baseline,'note':'Test data must not be retuned or rerun.'}))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gold',required=True,help='Real student-authored human-verified JSONL, NOT practice_question_ideas.jsonl')
    p.add_argument('--manifest',default='data/raw/manifest.jsonl')
    p.add_argument('--normalized',default='data/normalized.jsonl')
    p.add_argument('--baseline',choices=tuple(BASELINES),required=True)
    p.add_argument('--split',choices=('dev','test'),default='dev')
    p.add_argument('--confirm-test-once',action='store_true')
    p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(run(a),indent=2))
