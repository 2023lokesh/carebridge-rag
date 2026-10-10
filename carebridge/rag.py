"""Retrieval, trace, grounded extractive answer, optional cross-encoder rerank.

The bundled demo uses TF-IDF as a lightweight dense *proxy*, not neural embeddings.
For the graded full path, see carebridge/index.py for SentenceTransformer/Chroma.
"""
import math
import os
import re
from collections import Counter
from functools import lru_cache
from time import perf_counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .corpus import demo_documents, load_documents, tokenize
from .safety import screen_query, safe_document_text

STOP = set('what which when who why how does do did is are a an the of and for to with in on from can you me my please explain tell about your i it they differ difference between vs versus'.split())

@lru_cache(maxsize=4)
def _index(path=""):
    docs = load_documents(path or None)
    docs = [x for x in docs if safe_document_text(x["text"])]
    # Include title/section to improve matching vaccine acronyms in question text.
    texts = [x["title"] + " " + x.get("section", "") + " " + x["text"] for x in docs]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    vectors = vectorizer.fit_transform(texts)
    tokens = [tokenize(t) for t in texts]
    avg = sum(map(len, tokens)) / max(1, len(tokens))
    df = Counter(word for doc in tokens for word in set(doc))
    return docs, vectorizer, vectors, tokens, df, avg

def _bm25(qtokens, tokens, df, avg):
    n = len(tokens)
    out = []
    for doc in tokens:
        freq = Counter(doc)
        score = 0.0
        for q in set(qtokens):
            f = freq[q]
            if not f: continue
            idf = math.log(1 + (n - df[q] + .5) / (df[q] + .5))
            score += idf * (f * 2.2) / (f + 1.2*(.25 + .75*len(doc)/max(avg, 1)))
        out.append(score)
    return out

def retrieve(question, mode="hybrid", candidate_k=20, corpus_path="", rerank=False):
    if mode not in {"bm25", "dense", "hybrid"}:
        raise ValueError("mode must be bm25, dense, or hybrid")
    t0=perf_counter()
    docs, vectorizer, vectors, tokens, df, avg = _index(corpus_path)
    if not docs:
        return [], {"latency_ms":0.0,"mode":mode,"candidates":0}
    qtokens = tokenize(question)
    dense = cosine_similarity(vectorizer.transform([question]), vectors)[0].tolist()
    bm25 = _bm25(qtokens, tokens, df, avg)
    sorted_dense = sorted(range(len(docs)),key=lambda i:dense[i],reverse=True)
    sorted_bm = sorted(range(len(docs)),key=lambda i:bm25[i],reverse=True)
    rd = {idx:rank for rank,idx in enumerate(sorted_dense,1)}
    rb = {idx:rank for rank,idx in enumerate(sorted_bm,1)}
    if mode == "dense":
        combined = dense
    elif mode == "bm25":
        combined = bm25
    else:
        combined = [1/(60+rd[i]) + 1/(60+rb[i]) for i in range(len(docs))]
    order = sorted(range(len(docs)),key=lambda i:combined[i],reverse=True)[:candidate_k]
    results = []
    for i in order:
        results.append({**docs[i], "dense_score":round(dense[i],5),"bm25_score":round(bm25[i],5),"pre_score":round(combined[i],6),"post_score":None})
    if rerank and os.environ.get("CAREBRIDGE_RERANK", "off") == "cross-encoder":
        # Optional model download: enable only after installing requirements-full.txt.
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(os.environ.get("CAREBRIDGE_RERANK_MODEL","cross-encoder/ms-marco-MiniLM-L-6-v2"))
        scores = model.predict([[question,r["text"]] for r in results])
        for r, score in zip(results, scores): r["post_score"] = float(score)
        results.sort(key=lambda x:x["post_score"],reverse=True)
    else:
        # Label fallback transparently: no cross-encoder/model claimed.
        for r in results:
            r["post_score"] = round(.65*r["dense_score"] + .35*min(r["bm25_score"]/8,1),6)
        results.sort(key=lambda x:x["post_score"],reverse=True)
    return results, {"latency_ms":round((perf_counter()-t0)*1000,2), "mode":mode,
                     "candidates":len(results),"reranker":"cross-encoder" if rerank and os.getenv("CAREBRIDGE_RERANK") == "cross-encoder" else "lightweight lexical proxy",
                     "dense_engine":"TF-IDF proxy (demo)"}

def _relevant(q, result):
    words = set(tokenize(q)) - STOP
    title = set(tokenize(result["title"]+" "+result.get("section","")))
    text = set(tokenize(result["text"]))
    overlap = words & (text | title)
    # Stop rejecting short queries, but require a salient query token to appear in evidence.
    return bool(overlap) and (result["dense_score"] >= .065 or result["bm25_score"] >= .9)

def answer(question: str, mode="hybrid", corpus_path="", rerank=False, history=None):
    question = question.strip()
    if not question:
        return {"answer":"Please enter a general vaccine-information question.","refused":True,"sources":[],"trace":[]}
    block = screen_query(question)
    if block:
        return {"answer":block,"refused":True,"sources":[],"trace":[],"reason":"clinical_safety"}
    # Follow-up coreference, without holding private medical history.
    resolved = question
    if history and re.search(r"\b(it|that|this|those|they)\b", question, re.I):
        prev = next((h.get("question", "") for h in reversed(history[-3:]) if h.get("question")), "")
        resolved = prev + " " + question
    if os.environ.get("CAREBRIDGE_BACKEND", "demo")=="full":
        from .full_backend import retrieve_full
        pool, stats = retrieve_full(resolved,mode,20,rerank=True)
    else:
        pool, stats = retrieve(resolved,mode,20,corpus_path,rerank)
    eligible = [r for r in pool if _relevant(resolved, r)]
    # A safety filter avoids answering out-of-scope or ambiguous queries with filler excerpts.
    content_words = set(tokenize(resolved)) - STOP
    if not eligible or not content_words:
        return {"answer":"I do not have enough information in the approved CDC material to answer that question. Please consult current CDC guidance or a licensed healthcare professional.","refused":True,"sources":[],"trace":pool,"stats":stats,"reason":"insufficient_evidence"}
    # Use original, visibly cited educational paraphrases in the local demo. Limit 3 evidence units.
    selected=[]; seen=set()
    for r in eligible:
        key=(r["url"],r.get("section",""))
        if key not in seen:
            selected.append(r);seen.add(key)
        if len(selected)==3:break
    # Avoid unrelated evidence: require subject-specific tokens when a vaccine name appears.
    normalized = resolved.lower()
    vaccines = [x for x in ("hpv","mmrv","mmr","tdap","shingles","zoster","vis") if re.search(r"\b"+x+r"\b", normalized)]
    if vaccines:
        narrowed=[r for r in selected if any(re.search(r"\b"+v+r"\b",(r["title"]+" "+r["text"]).lower()) for v in vaccines)]
        if narrowed: selected=narrowed
    if not selected:
        return {"answer":"I don't have enough reliable CDC context for that question.","refused":True,"sources":[],"trace":pool,"stats":stats}
    answer_lines=[];sources=[]
    for i, r in enumerate(selected,1):
        # Paraphrases in bundled demo; for crawled text use a short attributed excerpt.
        if corpus_path:
            excerpt=" ".join(r["text"].split()[:22]) + ("…" if len(r["text"].split())>22 else "")
            phrasing=f"CDC source excerpt: “{excerpt}”"
        else:
            phrasing=r["text"]
        answer_lines.append(f"{phrasing} [{i}]")
        sources.append({"id":i,"url":r["url"],"title":r["title"],"updated":r.get("updated","not supplied"),"chunk_id":r["chunk_id"]})
    final_answer="\n\n".join(answer_lines)
    if os.getenv("CAREBRIDGE_GENERATION","extractive")=="openai" and os.getenv("OPENAI_API_KEY"):
        from .generate import generate_answer
        generated=generate_answer(resolved,selected)
        if generated is None:
            return {"answer":"I do not have enough verified source support to answer that question. Please refer to current CDC pages or a clinician.","refused":True,"sources":[],"trace":pool,"stats":stats,"reason":"citation_validation"}
        final_answer=generated
    return {"answer":final_answer,"refused":False,"sources":sources,
            "trace":pool,"stats":stats,"disclaimer":"Educational information only. Confirm current CDC editions; patient-specific decisions require a clinician."}
