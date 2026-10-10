"""Versioned Chroma re-chunk migration: no re-crawl, atomic active-pointer swap.

Requires requirements-full.txt and saved normalized.jsonl. Validates zero orphan
chunk IDs, then switches active collection. A failed build leaves old active intact.
"""
import argparse
import hashlib
import json
import os
import statistics
from pathlib import Path
from .corpus import chunk_documents,load_documents

def chunk_stats(chunks):
    sizes=sorted(len(c['text'].split()) for c in chunks)
    return {'chunks':len(chunks),'p50_words':statistics.median(sizes) if sizes else None,
            'p95_words':sizes[min(len(sizes)-1,round((len(sizes)-1)*.95))] if sizes else None,
            'min_words':min(sizes) if sizes else None, 'max_words':max(sizes) if sizes else None}

def rebuild(corpus,db_dir='data/chroma',strategy='heading',collection_name='carebridge'):
    import chromadb
    from sentence_transformers import SentenceTransformer
    if strategy not in {'fixed','heading'}:raise ValueError('Unknown chunking strategy')
    corpus=Path(corpus);db_dir=Path(db_dir)
    model_name='sentence-transformers/all-MiniLM-L6-v2'
    model=SentenceTransformer(model_name)
    fixed_size, fixed_overlap = 180, 30
    normalized = load_documents(corpus)
    chunks=chunk_documents(normalized,strategy,size=fixed_size if strategy=="fixed" else 450,overlap=fixed_overlap if strategy=="fixed" else 75)
    if not chunks:raise ValueError('No normalized chunks available: refusing empty index')
    ids=[r['chunk_id'] for r in chunks]
    if len(ids)!=len(set(ids)):raise ValueError('Deterministic chunk IDs must be unique')
    digest=hashlib.sha256(corpus.read_bytes()+strategy.encode()).hexdigest()[:16]
    active_name=f'{collection_name}_{strategy}_{digest}'
    db_dir.mkdir(parents=True,exist_ok=True)
    client=chromadb.PersistentClient(path=str(db_dir))
    pointer=db_dir/'active_index.json'
    old=json.loads(pointer.read_text()) if pointer.exists() else {}
    # Create new immutable version: old collection remains queryable until finished.
    coll=client.get_or_create_collection(name=active_name,metadata={'hnsw:space':'cosine'})
    present=coll.get(include=[])['ids']
    if present:coll.delete(ids=present)   # Only resets the *new version* on retries.
    for start in range(0,len(chunks),64):
        batch=chunks[start:start+64]
        embeddings=model.encode([x['text'] for x in batch],normalize_embeddings=True).tolist()
        coll.upsert(ids=[r['chunk_id'] for r in batch],documents=[r['text'] for r in batch],
            embeddings=embeddings,metadatas=[{'url':r['url'],'title':r['title'],
                 'page_type':r.get('page_type','html'),'section':r.get('section',''),
                 'strategy':strategy} for r in batch])
    actual=set(coll.get(include=[])['ids']);expected=set(ids)
    if actual!=expected:raise AssertionError(f'Index mismatch: orphans={len(actual-expected)}, missing={len(expected-actual)}')
    model_token_lengths=[]
    for start in range(0,len(chunks),128):
        model_token_lengths.extend(model.tokenizer([x["text"] for x in chunks[start:start+128]],truncation=False,padding=False,return_length=True)["length"])
    ordered_token_lengths=sorted(model_token_lengths)
    model_limit=int(model.max_seq_length)
    row={'strategy':strategy,'collection':active_name,'corpus_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),
         'chunks':len(chunks),'ids_verified':len(actual),'orphans':0,
         'model':model_name,'dimension':384,'metric':'cosine','l2_normalized':True,
         'source_rows':len(normalized),'source_urls':len({x["url"] for x in chunks}),
         'fixed_window_words':fixed_size if strategy=="fixed" else None,
         'fixed_overlap_words':fixed_overlap if strategy=="fixed" else None,
         'model_max_seq_length':model_limit,
         'p50_model_tokens':statistics.median(ordered_token_lengths),
         'p95_model_tokens':ordered_token_lengths[min(len(ordered_token_lengths)-1,round((len(ordered_token_lengths)-1)*.95))],
         'chunks_over_model_limit':sum(x>model_limit for x in model_token_lengths),
         'token_length_proxy':'Whitespace counts; model tokenizer separately measured',**chunk_stats(chunks)}
    # Swap manifests only after index verification; do not overwrite when failed.
    chunk_out=db_dir/'active_chunks.jsonl'
    staging=db_dir/'active_chunks.staging'
    staging.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in chunks))
    staging.replace(chunk_out)
    tmp=pointer.with_suffix('.pending.json');tmp.write_text(json.dumps(row,indent=2))
    tmp.replace(pointer)
    if old.get('collection') and old['collection']!=active_name:
        client.delete_collection(old['collection'])
    (db_dir/'index_build.json').write_text(json.dumps(row,indent=2))
    return row

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--corpus',default='data/normalized.jsonl');p.add_argument('--strategy',choices=('fixed','heading'),default='heading');p.add_argument('--db-dir',default='data/chroma')
    a=p.parse_args();print(json.dumps(rebuild(a.corpus,a.db_dir,a.strategy),indent=2))
