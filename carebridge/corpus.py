"""Canonical source records, deterministic IDs, two chunking strategies."""
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DEMO = BASE / "data" / "demo_sources.json"

def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(str(x) for x in parts).encode()).hexdigest()[:20]

def demo_documents():
    data = json.loads(DEMO.read_text(encoding="utf-8"))
    for row in data:
        row["doc_id"] = stable_id(row["url"])
        row["chunk_id"] = stable_id(row["url"], row["section"], row["text"])
        row["page_type"] = "html"
    return data

def load_documents(path: str | Path | None = None):
    if path is None:
        return demo_documents()
    path = Path(path)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def tokenize(text: str):
    return re.findall(r"[a-z0-9]+", text.lower())

def chunk_documents(documents, strategy="fixed", size=450, overlap=75, min_size=1):
    if strategy not in {"fixed", "heading"}:
        raise ValueError("Unknown chunk strategy")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be >= 0 and < size")
    output = []
    seen_chunk_ids = set()
    for doc in documents:
        text = doc["text"].strip()
        if not text:
            continue
        if strategy == "heading":
            # The extractor emits separate headings/sections. Splitting long sections retains heading metadata.
            parts = re.split(r"(?m)(?=^#{1,5} )", text)
            windows = []
            for p in parts:
                tokens = p.split()
                for start in range(0, len(tokens), 650):
                    windows.append(" ".join(tokens[start:start+650]))
        else:
            tokens = text.split()
            windows = [" ".join(tokens[i:i+size]) for i in range(0, len(tokens), size-overlap)]
        for idx, window in enumerate(windows):
            if len(window.split()) < min_size:
                continue
            row = {**doc, "text":window,"strategy":strategy,"index":idx}
            row["chunk_id"] = stable_id(doc.get("doc_id") or doc["url"],doc.get("section",""),doc.get("page_type",""),strategy,str(idx),window)
            if row["chunk_id"] in seen_chunk_ids:
                continue
            seen_chunk_ids.add(row["chunk_id"])
            output.append(row)
    return output
