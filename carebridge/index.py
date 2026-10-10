"""Real dense embedding and persistent Chroma index with stale-chunk deletion.

Requires: pip install -r requirements-full.txt
python -m carebridge.index --corpus data/normalized.jsonl --strategy heading
"""
import argparse
import json
from pathlib import Path
from .corpus import chunk_documents,load_documents

def rebuild(corpus,db_dir="data/chroma",strategy="heading",collection_name="carebridge"):
    import numpy as np
    import chromadb
    from sentence_transformers import SentenceTransformer
    model_name="sentence-transformers/all-MiniLM-L6-v2"
    model=SentenceTransformer(model_name)
    chunks=chunk_documents(load_documents(corpus),strategy)
    db=chromadb.PersistentClient(path=db_dir)
    collection=db.get_or_create_collection(name=collection_name,metadata={"hnsw:space":"cosine"})
    existing=collection.get(include=[])["ids"]
    # Delete stale chunks BEFORE inserting the new strategy; explicitly verify no old IDs survive.
    if existing:collection.delete(ids=existing)
    assert collection.count()==0,"Failed to delete previous chunk IDs"
    for start in range(0,len(chunks),64):
        batch=chunks[start:start+64]
        embeddings=np.asarray(model.encode([x["text"] for x in batch],normalize_embeddings=True),dtype=float)
        collection.upsert(ids=[r["chunk_id"] for r in batch],documents=[r["text"] for r in batch],
             embeddings=embeddings.tolist(),metadatas=[{"url":r["url"],"title":r["title"],"page_type":r.get("page_type","html"),
             "section":r.get("section",""),"strategy":strategy} for r in batch])
    with (Path(db_dir).parent/"active_chunks.jsonl").open("w",encoding="utf-8") as manifest:
        for row in chunks:manifest.write(json.dumps(row,ensure_ascii=False)+"\n")
    current=set(collection.get(include=[])["ids"])
    expected={r["chunk_id"] for r in chunks}
    if current!=expected:raise AssertionError(f"Orphan mismatch: unexpected {len(current-expected)}, missing {len(expected-current)}")
    summary={"strategy":strategy,"chunks":len(chunks),"ids_verified":len(current),"orphans":len(current-expected),
             "model":model_name,"dimension":384,"metric":"cosine","l2_normalized":True}
    Path(db_dir).mkdir(exist_ok=True,parents=True)
    (Path(db_dir)/"index_build.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--corpus",default="data/normalized.jsonl");p.add_argument("--strategy",choices=["fixed","heading"],default="heading");p.add_argument("--db-dir",default="data/chroma")
    a=p.parse_args();print(json.dumps(rebuild(a.corpus,a.db_dir,a.strategy),indent=2))
