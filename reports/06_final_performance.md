# 06 — Measured performance and grading gaps

**Development retrieval and B0–B3 generated-answer runs actually completed; human-score QA and sealed TEST remain pending** as of October 10, 2026.

### Real archived sources and indexes
- CDC: **165 raw pages; 163 distinct normalized CDC pages; 35 PDFs; 13 table-bearing HTML pages; 3,063 normalized blocks; no crawl errors or raw hash mismatches**. [Run #38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533).
- MiniLM/Chroma cosine: **3,477 fixed** / **3,301 heading-aware** tokenizer-safe chunks; zero orphan/missing/over-limit output chunks, same source snapshot, no re-crawl. [Run #38059975329](https://github.com/2023lokesh/carebridge-rag/actions/runs/38059975329).
- Frozen evaluation: **24 DEV / 16 sealed TEST** out of 40 team-attested reviewed, originally AI-assisted questions. DEV-only workflow authenticated zero TEST records.

### B1/B2/B3 *retrieval-only* DEV results
[Successful run #38062665587](https://github.com/2023lokesh/carebridge-rag/actions/runs/38062665587), **18 source-URL-labelled DEV questions**. Per-question relevance is **source-URL match**, not reviewed chunk/claim entailment.

| Metric | B1 BM25 fixed | B2 MiniLM fixed | B3 heading hybrid+cross-encoder |
| --- | ---: | ---: | ---: |
| Recall@5 | 0.6944 | 0.8056 | **0.8889** |
| Recall@20 | 0.9444 | **1.0000** | **1.0000** |
| MRR | 0.5903 | **0.7469** | 0.7231 |
| nDCG@10 | 0.6305 | **0.7757** | 0.7463 |
| p50 warm retrieval (ms) | 88.59 | **14.93** | 928.93 |
| p95 warm retrieval (ms) | 93.09 | **17.96** | 988.44 |

The measured query timings exclude startup, generator inference, network latency and compute cost. The lexical baseline recomputes tokenization per query; latency differences are implementation-specific. B3 wins top-five source recall; B2 wins MRR/nDCG and warm retrieval time.

**Paired 95% bootstrap Recall@5 intervals** (2,000 replicates; seed 633; same 18 items): B1→B2 gain +0.1111 **[-0.1667, 0.3889]**, B1→B3 +0.1944 **[-0.0556, 0.4444]**, B2→B3 +0.0833 **[-0.0278, 0.2222]**. One-factor within-B3 cross-encoder RRF-candidate reranking gain +0.0833 **[-0.1111, 0.2778]**; MRR changes -0.0204. **All nonzero intervals cross zero; no confirmed gain at 95% confidence.** See `reports/04_retrieval_reranking.md`.

### Still outstanding; do not invent
1. **COMPLETED:** Actual B0 closed-book and 24×4 B1/B2/B3 generated-answer runs in [workflow #38066174591](https://github.com/2023lokesh/carebridge-rag/actions/runs/38066174591): all 96 model responses, zero TEST items, and automated cold-excluded latency/citation/abstention diagnostics. **Unresolved:** The team-entered human judgments require QA after reconciliation with the original model outputs; see [generation evidence and review audit](05_generation.md).
2. Team-entered **96 human rating rows** exist, but inconsistencies with the actual generated answers prevent release of validated factual/citation/refusal/clinical-safety rates. Correct all audit flags, document failure labels, and compute paired human correctness CIs plus B0-correct/B0-incorrect subset analysis. Warm total-generation latency is already measured (see report 05); compute cost remains unmonetized.
3. **>=15 genuine manually classified failures**, documented adversarial injection, staleness checks, full deployed neural backend parity, metadata filtering demonstrations.
4. The **one-time 16-item TEST run**, only *after* DEV selection is frozen and approval obtained. Do not peek or repeatedly tune on TEST.
5. Course instructor ruling about AI-assisted original gold questions and Friday-before-chatbot independent student authorship; do not backdate.
6. Main branch protection enforcement and substantive per-teammate multi-stage GitHub contribution evidence.

Preserve original GitHub artifacts (retrieval, raw crawl and both indexes) before **October 17, 2026**. The public live demo remains small-corpus rather than the fully indexed 163-page system.
