# CareBridge 9-minute residency demo — speaking notes

**0:00–1:00** Introduce general CDC vaccine education, not personal medical decision support. State that a credible-looking uncited answer can be harmful.

**1:00–2:10** Show the public FastAPI/Render *small-corpus* demo if live: history-aware chat, clickable CDC links, expandable trace, visible refusal; do not claim full indexed deployment.

**2:10–3:20** GitHub real crawl [#38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533): 165 raw / 163 normalized CDC pages, 35 PDFs, 13 table HTML, 3,063 blocks, hash checks, robots and rate limit.

**3:20–4:40** Two Chroma MiniLM cosine indexes (384-dim): 3,477 fixed/3,301 heading-aware chunks; tokenizer cap, deterministic IDs, zero orphan IDs, no recrawl.

**4:40–6:20** Real DEV retrieval run #38062665587 (24 DEV, 0 TEST; 18 URL-labelled answerable). Recall@5 B1 69.44%, B2 80.56%, B3 88.89%; Recall@20 94.44%, 100%, 100%. B2 has better MRR/nDCG and lower measured retrieval latency. No Recall@5 improvement statistically established at 95%.

**6:20–7:30** Ethics: CDC allowlist, PII/personal-medical refusal, emergency referrals, detection of prompt overrides, stale CDC source risks. Discuss actual two polio/varicella false refusals and fixed regression.

**7:30–8:30** Show **approved/merged PR #14** for same-generator B0–B3 code; do not claim generated-answer accuracy or human judgments until actually performed. Human scoring will cover 96 DEV outputs, citations and correct refusals.

**8:30–9:00** Acknowledge the 16 sealed TEST (not run), AI-assisted golden origins / Oct 10 self-review, course sequencing discrepancy, evidence and remaining human/clinical work. Invite Q&A on chunk IDs, BM25, RRF, cosine similarity and paired bootstrap uncertainty.

**Bring:** raw crawl/index/eval Actions URLs; reports 01–07; a real refusal screenshot; independent team review proof; private golden workbook only via authorized instructor channel.
