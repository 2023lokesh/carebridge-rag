"""Ethical CDC crawler: robots.txt, ≤1 req/sec, raw archive before parsing.

Usage: python -m carebridge.crawler --contact you@school.edu --max-pages 150
Only a human-approved contact address should be provided; no example email is sent.
"""
import argparse
import hashlib
import json
import re
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from .safety import safe_url

# Distinct public information and PDF seed URLs; robots.txt can still deny any seed.
# Having seeds is not proof of successful download/ingestion.
SEEDS = (
    "https://www.cdc.gov/vaccines/hcp/current-vis/index.html",
    "https://www.cdc.gov/iis/code-sets/vis-url-table.html",
    "https://www.cdc.gov/vaccines/hcp/current-vis/mmr.html",
    "https://www.cdc.gov/vaccines/hcp/current-vis/mmrv.html",
    "https://www.cdc.gov/vaccines/hcp/current-vis/tdap.html",
    "https://www.cdc.gov/vaccines/hcp/current-vis/hpv.html",
    "https://www.cdc.gov/vaccines/hcp/current-vis/shingles.html",
    "https://www.cdc.gov/vaccines/hcp/current-vis/downloads/mmr.pdf",
    "https://www.cdc.gov/vaccines/hcp/current-vis/downloads/mmrv.pdf",
    "https://www.cdc.gov/vaccines/hcp/current-vis/downloads/tdap.pdf",
    "https://www.cdc.gov/vaccines/hcp/current-vis/downloads/hpv.pdf",
    "https://www.cdc.gov/vaccines/hcp/current-vis/downloads/shingles-recombinant.pdf",
)

def _timestamp():
    return datetime.now(timezone.utc).isoformat()

class EthicalCrawler:
    def __init__(self,contact: str,out="data/raw",interval=1.15,timeout=20):
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",contact):
            raise ValueError("Supply a real contact email for the descriptive User-Agent")
        self.agent=f"CareBridgeMSAI633Crawler/0.1 (academic research; contact: {contact})"
        self.session=requests.Session()
        self.session.headers.update({"User-Agent":self.agent})
        self.interval=max(interval,1.0)
        self.last_call=0.0
        self.timeout=timeout
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
        self.robots=RobotFileParser()
        self.robots_url="https://www.cdc.gov/robots.txt"
        self.ready=False
    def _throttle(self):
        delay=self.interval-(time.monotonic()-self.last_call)
        if delay>0:time.sleep(delay)
        self.last_call=time.monotonic()
    def load_robots(self):
        self._throttle()
        response=self.session.get(self.robots_url,timeout=self.timeout)
        response.raise_for_status()  # Fail closed if robots unavailable.
        self.robots.parse(response.text.splitlines())
        self.ready=True
    def permitted(self,url):
        return self.ready and safe_url(url) and self.robots.can_fetch(self.agent,url)
    def fetch(self,url):
        if not self.permitted(url):return None
        self._throttle()
        try: resp=self.session.get(url,timeout=self.timeout,allow_redirects=False)
        except requests.RequestException:return None
        if resp.status_code in (429,503):
            value=resp.headers.get("Retry-After", "")
            if value.isdigit():time.sleep(min(int(value),60))
            return None
        if resp.status_code!=200:return None
        if len(resp.content)>12*1024*1024:return None
        content_type=resp.headers.get("Content-Type","").split(";")[0].lower()
        if content_type not in ("text/html","application/pdf"):return None
        raw_hash=hashlib.sha256(resp.content).hexdigest()
        rel=f"{raw_hash}.bin"
        raw_path=self.out/rel
        if not raw_path.exists():raw_path.write_bytes(resp.content)
        meta={"source_url":url,"crawl_timestamp":_timestamp(),"status":resp.status_code,
              "mime_type":content_type,"raw_sha256":raw_hash,"raw_path":str(raw_path)}
        with (self.out/"manifest.jsonl").open("a",encoding="utf-8") as f:
            f.write(json.dumps(meta)+"\n")
        return meta,resp.content
    def crawl(self,max_pages=150):
        self.load_robots()
        q=deque(SEEDS);seen=set();success=0
        while q and success<max_pages:
            u=q.popleft().split("#")[0]
            if u in seen or not self.permitted(u):continue
            seen.add(u)
            fetched=self.fetch(u)
            if not fetched:continue
            meta,raw=fetched
            success+=1
            if meta["mime_type"]!="text/html":continue
            soup=BeautifulSoup(raw,"html.parser")
            for link in soup.select("a[href]"):
                href=link.get("href","")
                nxt,_=urldefrag(urljoin(u,href))
                nxt=nxt.split("?")[0]
                if safe_url(nxt) and nxt not in seen and nxt not in q:q.append(nxt)
        return {"stored":success,"visited":len(seen),"queued_unvisited":len(q),"robots_url":self.robots_url}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contact",required=True);p.add_argument("--max-pages",type=int,default=150);p.add_argument("--out",default="data/raw")
    a=p.parse_args()
    print(json.dumps(EthicalCrawler(a.contact,out=a.out).crawl(a.max_pages),indent=2))
