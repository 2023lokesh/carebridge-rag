"""Actual machine exploratory diagnostics. NOT B0-B3 graded measurements.

Uses AI-suggested practice prompts and small curated DEMO text; a question/URL
match here is not human-verified correctness. Never run on the held-out set.
"""
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path
from carebridge.rag import retrieve, answer


def run(path='data/practice_question_ideas.jsonl'):
    items=[json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    answerable=[q for q in items if q['category'] in ('single_hop','multi_hop','comparative','temporal')]
    result={'scope':'exploratory development smoke test, NOT independently human-verified and NOT B0-B3',
            'total_questions':len(items),'answerable_practice_questions':len(answerable),
            'neural_dense_available':False,'full_reranker_available':False,'closed_book_model_run':False}
    for mode in ('bm25','dense','hybrid'):
        hits5=0;hits20=0;mrr=0;times=[]
        for item in answerable:
            started=time.perf_counter(); docs,_=retrieve(item['question'],mode,20);times.append((time.perf_counter()-started)*1000)
            allowed=set(item['candidate_source_urls'])
            ranks=[i for i,d in enumerate(docs,1) if d['url'] in allowed]
            if ranks:
                mrr+=1/ranks[0];hits20+=1;hits5+=ranks[0]<=5
        def pct(p):
            if not times:return None
            s=sorted(times);return round(s[min(len(s)-1,round((len(s)-1)*p))],2)
        n=len(answerable)
        result[mode]={'engine':{'bm25':'lexical BM25','dense':'TF-IDF proxy, NOT neural embedding','hybrid':'BM25 + TF-IDF proxy, NOT graded B3'}[mode],
                      'candidate_URL_hit_at_5':round(hits5/n,4),'candidate_URL_hit_at_20':round(hits20/n,4),
                      'candidate_URL_mrr_proxy':round(mrr/n,4),'p50_retrieval_ms':pct(.5),'p95_retrieval_ms':pct(.95)}
    # Answers may legitimately refuse (unanswerable or medical); not scored as correctness.
    result['responded']=len(items)
    result['refusals']=sum(bool(answer(item['question'])['refused']) for item in items)
    return result

if __name__=='__main__':
    data=run();dest=Path('reports/practice_diagnostics.json');dest.parent.mkdir(exist_ok=True,parents=True)
    dest.write_text(json.dumps(data,indent=2))
    print(json.dumps(data,indent=2))
