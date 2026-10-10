"""Optional full graded retriever: neural dense Chroma + BM25 + RRF + cross-encoder.
This is NOT used by the lightweight demo unless CAREBRIDGE_BACKEND=full.
"""
import json
import math
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from .corpus import tokenize

@lru_cache(maxsize=1)
def _loaded():
    import chromadb
    from sentence_transformers import SentenceTransformer
    root=Path(__file__).resolve().parents[1]
    folder=root / os.environ.get("CAREBRIDGE_DB_DIR","data/chroma")
    pointer=json.loads((folder / "active_index.json").read_text(encoding="utf8"))
    paths=folder / "active_chunks.jsonl"
    docs=[json.loads(x) for x in paths.read_text(encoding="utf-8").splitlines() if x.strip()]
    client=chromadb.PersistentClient(path=str(folder))
    collection=client.get_collection(pointer["collection"])
    model=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return docs,collection,model

def _bm25(query,doc_tokens):
    n=len(doc_tokens)
    df=Counter(w for doc in doc_tokens for w in set(doc))
    avg=sum(map(len,doc_tokens))/max(1,n)
    result=[]
    for toks in doc_tokens:
        count=Counter(toks);score=0.0
        for word in set(query):
            freq=count[word]
            if freq:
                score+=math.log(1+(n-df[word]+.5)/(df[word]+.5))*freq*2.2/(freq+1.2*(.25+.75*len(toks)/max(1,avg)))
        result.append(score)
    return result

def retrieve_full(question,mode="hybrid",candidate_k=20,rerank=True,page_type=None):
    t0=perf_counter()
    docs,coll,model=_loaded()
    terms=tokenize(question)
    scores_bm=_bm25(terms,[tokenize(d["title"]+" "+d["text"]) for d in docs])
    bmranks=sorted(range(len(docs)),key=lambda idx:scores_bm[idx],reverse=True)
    by_id={d["chunk_id"]:i for i,d in enumerate(docs)}
    qvec=model.encode([question],normalize_embeddings=True)[0].tolist()
    args={"query_embeddings":[qvec],"n_results":min(max(20,candidate_k),coll.count()),"include":["distances"]}
    if page_type:args["where"]={"page_type":page_type}
    found=coll.query(**args)
    dense_ids=found["ids"][0]
    dists=found["distances"][0]
    dense_ranks={by_id[chunk_id]:rank for rank,chunk_id in enumerate(dense_ids,1) if chunk_id in by_id}
    cosine_scores={by_id[chunk_id]:max(0.0,1-dist) for chunk_id,dist in zip(dense_ids,dists) if chunk_id in by_id}
    bm_ranks={idx:rank for rank,idx in enumerate(bmranks,1)}
    if mode=="dense": candidates=set(dense_ranks)
    elif mode=="bm25":candidates=set(bmranks[:max(20,candidate_k)])
    else:candidates=set(dense_ranks)|set(bmranks[:max(20,candidate_k)])
    def rank_score(idx):
        if mode=="bm25":return scores_bm[idx]
        if mode=="dense":return cosine_scores.get(idx,0)
        return (1/(60+dense_ranks[idx]) if idx in dense_ranks else 0)+(1/(60+bm_ranks[idx]) if idx in bm_ranks else 0)
    order=sorted(candidates,key=rank_score,reverse=True)[:max(20,candidate_k)]
    results=[]
    for idx in order:
        r={**docs[idx],"dense_score":round(cosine_scores.get(idx,0),5),"bm25_score":round(scores_bm[idx],5),"pre_score":round(rank_score(idx),6)}
        r["post_score"]=None; results.append(r)
    rerank_name="not enabled"
    if rerank and results:
        from sentence_transformers import CrossEncoder
        rerank_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
        ce=CrossEncoder(rerank_name)
        predictions=ce.predict([[question,d["text"]] for d in results])
        for d,p in zip(results,predictions):d["post_score"]=float(p)
        results.sort(key=lambda r:r["post_score"],reverse=True)
    return results,{"latency_ms":round((perf_counter()-t0)*1000,2),"mode":mode,
                    "candidates":len(results),"reranker":rerank_name,"dense_engine":"all-MiniLM-L6-v2 / Chroma cosine"}
