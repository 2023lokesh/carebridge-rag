"""Convert saved raw HTML/PDF bytes to normalized JSONL, preserving HTML tables."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import fitz
from .corpus import stable_id
from .safety import safe_document_text, safe_url

def normalize_html(raw):
    soup=BeautifulSoup(raw,"html.parser")
    for tag in soup.select("nav,footer,header,script,style,aside,form,iframe,[role=navigation]"):
        tag.decompose()
    title=soup.title.get_text(" ",strip=True) if soup.title else "CDC page"
    main=soup.find("main") or soup.find("article") or soup.body or soup
    blocks=[];heading="General"
    for tag in main.find_all(["h1","h2","h3","h4","p","ul","ol","table"],recursive=True):
        if tag.name.startswith("h"):
            heading=tag.get_text(" ",strip=True)
        elif tag.name=="table":
            rows=[]
            for tr in tag.find_all("tr"):
                cols=[c.get_text(" ",strip=True) for c in tr.find_all(["th","td"],recursive=False)]
                if cols:rows.append(" | ".join(cols))
            if rows:
                blocks.append({"section":heading,"text":"\n".join(rows),"is_table":True})
        elif tag.name in ("p","ul","ol"):
            if tag.find_parent("table"):continue
            text=tag.get_text(" ",strip=True)
            if len(text.split()) >= 7:
                blocks.append({"section":heading,"text":text,"is_table":False})
    return title,blocks

def normalize_pdf(raw):
    pages=[]
    with fitz.open(stream=raw,filetype="pdf") as pdf:
        for i,p in enumerate(pdf):
            text=p.get_text("text",sort=True).strip()
            if text:
                pages.append({"section":f"PDF page {i+1}","text":text,"is_table":False})
    return "CDC PDF resource",pages

def extract_manifest(manifest="data/raw/manifest.jsonl",output="data/normalized.jsonl"):
    input_path=Path(manifest);seen=set();rows=[];skipped=[]
    for line in input_path.read_text(encoding="utf-8").splitlines():
        meta=json.loads(line); url=meta["source_url"]
        if not safe_url(url):skipped.append((url,"prohibited URL"));continue
        if meta["raw_sha256"] in seen:continue
        seen.add(meta["raw_sha256"])
        raw=Path(meta["raw_path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=meta["raw_sha256"]:raise ValueError("Raw content hash mismatch: "+url)
        try:
            if meta["mime_type"]=="application/pdf":
                title,blocks=normalize_pdf(raw);kind="pdf"
            else:
                title,blocks=normalize_html(raw);kind="html"
        except Exception as ex:
            skipped.append((url,str(ex)));continue
        # Avoid indexing pages with contact data, known prompt-injection directives or tiny extraction.
        for block in blocks:
            if not safe_document_text(block["text"]):continue
            if len(block["text"].split())<7:continue
            rows.append({"doc_id":stable_id(url),"url":url,"title":title,"section":block["section"],
                         "text":block["text"],"page_type":"table" if block["is_table"] else kind,
                         "crawl_timestamp":meta["crawl_timestamp"],"raw_sha256":meta["raw_sha256"],
                         "updated":"unverified", "chunk_id":stable_id(url,block["section"],block["text"])})
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    with open(output,"w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    return {"normalized_blocks":len(rows),"raw_documents_unique":len(seen),"excluded_blocks_or_files":len(skipped)}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--manifest",default="data/raw/manifest.jsonl");p.add_argument("--output",default="data/normalized.jsonl")
    a=p.parse_args();print(extract_manifest(a.manifest,a.output))
