"""Validate all embedded chunk IDs and one illustrative neural query."""
import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
def main():
    root=Path("data/chroma")
    meta=json.loads((root/"active_index.json").read_text())
    assert meta["strategy"]=="fixed"
    chunks=[json.loads(line) for line in (root/"active_chunks.jsonl").read_text().splitlines() if line]
    ids={x["chunk_id"] for x in chunks}
    assert len(ids)==len(chunks)
    coll=chromadb.PersistentClient(path=str(root)).get_collection(meta["collection"])
    assert set(coll.get(include=[])["ids"])==ids
    model=SentenceTransformer(meta["model"])
    question="What does the MMR vaccine protect against?"
    response=coll.query(query_embeddings=model.encode([question],normalize_embeddings=True).tolist(),n_results=5,include=["metadatas","distances"])
    assert response["ids"][0]
    urls=[x["url"] for x in response["metadatas"][0]]
    assert all(u.startswith("https://www.cdc.gov/") for u in urls)
    out={"chunks":len(chunks),"unique_pages":meta["source_urls"],"orphan_chunks":0,
         "model":meta["model"],"corpus_sha256":meta["corpus_sha256"],
         "query":question,"top5_urls":urls,"heldout_test_evaluated":False}
    Path("reports/fixed_index_smoke.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
