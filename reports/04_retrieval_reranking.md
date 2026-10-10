# 04 — Retrieval, ranking, and reranking: measured DEV results

**Status: B1/B2/B3 retrieval-only development evaluation completed on October 10, 2026.** This is **not** a complete graded end-to-end B0–B3 study, a held-out test evaluation, or a claim of statistically significant model improvement.

## Evidence and reproducibility

- [Successful GitHub Actions evaluation run #38062665587](https://github.com/2023lokesh/carebridge-rag/actions/runs/38062665587), commit `8f052c9ef1a685574324e5369c5c2768d3b425a4`.
- Artifact: `carebridge-development-retrieval-38062665587`, ID `11673119012`; expires **October 17, 2026**. Contains `B1.json`, `B2.json`, `B3.json`, and `paired_comparison.json`, including 18 per-question ID scores but no question/answer text.
- Fixed CDC crawl of **163 source pages**, 35 PDFs, 13 table-bearing HTML pages, originally collected by [run #38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533).
- Both token-safe indexes from [run #38059975329](https://github.com/2023lokesh/carebridge-rag/actions/runs/38059975329): fixed **3,477** chunks; heading-aware **3,301** chunks; zero oversized or orphan IDs.
- Frozen `data/frozen_split_manifest.json`, DEV payload SHA-256 `012677aa7a605316f2b0f5f9712b64d0b0c9deb3bd6f151b531e16ceededc6bf`. Workflow validated **24 DEV items, including 18 source-URL-labelled retrieval questions**. The **16 TEST questions were never loaded, scored, or exposed**. The 6 remaining DEV items need separate refusal/ambiguity scoring.

## Experimental conditions

- **B1:** exact Okapi BM25 retrieval over the fixed, tokenizer-safe 3,477 chunks, top 20.
- **B2:** real MiniLM (`all-MiniLM-L6-v2`) 384-dimensional cosine dense retrieval over the **same** fixed index, top 20.
- **B3:** heading-aware 3,301 chunks; BM25 + dense reciprocal rank fusion; cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2` reranks 20 candidates. Reports top-five and full-20 retrieval metrics.
- Relevance is derived from human-reviewed **source URLs**, not adjudicated ground-truth chunk IDs. A URL is credited only once per question. Metrics are retrieval-only: no generation was called.
- All measurements are from the same successful GitHub Actions run with models and Chroma indexes loaded ahead of per-query timing; latencies **exclude model initialization, API overhead, and answer generation**. B1 implementation recomputes corpus tokenization per query; do not interpret B2/B1 latency differences as a general property of neural versus lexical search.

## Measured aggregates (18 identical DEV queries)

| Metric | B1 BM25 | B2 neural dense | B3 hybrid + cross-encoder |
| --- | ---: | ---: | ---: |
| Recall@5 | 0.6944 | 0.8056 | **0.8889** |
| Recall@20 | 0.9444 | **1.0000** | **1.0000** |
| MRR | 0.5903 | **0.7469** | 0.7231 |
| nDCG@10 | 0.6305 | **0.7757** | 0.7463 |
| p50 measured retrieval latency (ms) | 88.59 | **14.93** | 928.93 |
| p95 measured retrieval latency (ms) | 93.09 | **17.96** | 988.44 |

B3 obtains **+19.44 percentage points** Recall@5 compared with B1 and **+8.33 points** compared with B2; B2 remains better on MRR, nDCG@10, and measured retrieval latency. Do not call B3 uniformly the best.

## Paired 95% bootstrap confidence intervals

Each paired difference is the mean of differences on the **same 18 DEV questions**; bootstrap resampling uses seed 633 and 2,000 replicates.

| Comparison | Metric | Delta | Paired 95% CI |
| --- | --- | ---: | --- |
| B1 → B2 | Recall@5 | +0.1111 | [-0.1667, +0.3889] |
| B1 → B2 | MRR | +0.1565 | [-0.0670, +0.3856] |
| B1 → B3 | Recall@5 | +0.1944 | [-0.0556, +0.4444] |
| B2 → B3 | Recall@5 | +0.0833 | [-0.0278, +0.2222] |
| B2 → B3 | MRR | -0.0237 | [-0.1524, +0.1146] |
| B1 → B2 | Recall@20 | +0.0556 | [0.0000, +0.1389] |

**None of these improvements is statistically established at the 95% level**, because the intervals include zero. Small sample size (18) and a ceiling in Recall@20 limit inference. All other comparisons and metrics are in the archived paired JSON.

## One-factor cross-encoder ablation (identical B3 candidate pool)

Compare B3 before cross-encoder reranking (BM25+dense RRF) versus after reranking, keeping **the same 20 heading-aware candidates**:

| Metric | Change due to reranking | Paired 95% CI |
| --- | ---: | --- |
| Recall@5 | **+0.0833** | [-0.1111, +0.2778] |
| Recall@20 | 0.0000 | [0.0000, 0.0000] |
| MRR | -0.0204 | [-0.1139, +0.0646] |
| nDCG@10 | -0.0140 | [-0.0980, +0.0709] |

The cross-encoder improved top-five source recall in this run, but slightly reduced rank-based MRR and nDCG. Differences are not statistically established. Comparisons between B1/B2 and B3 change several factors simultaneously; **only within-B3 pre/post reranking isolates the cross-encoder**. Added reranker-only milliseconds were not separately instrumented; B3 per-query time includes fusion and cross-encoder work, but is not a direct isolated reranker latency estimate.

## Limitations and remaining course deliverables

1. Original golden questions originated as **AI-assisted drafts with team-attested individual self-review**, not proven independently student-authored before chatbot construction. Preserve that chronology when reporting course compliance.
2. No **B0 closed-book generator** experiment and no controlled same-generator end-to-end B1/B2/B3 answer study.
3. No answer correctness, citation accuracy, helpful refusals, over-refusal, hallucination rate, clinical safety scoring, model/API cost, cold-start latency, or full end-to-end p50/p95.
4. Six DEV questions (unanswerable/ambiguous without gold source URLs) must be scored with an explicit refusal protocol, not silently counted as successful retrieval.
5. Perform additional one-factor ablations, >/=15 genuine human-labeled failure categories, and end-to-end statistical evaluation. Select a final system on DEV **before** one controlled run of the sealed 16-item TEST set. Do not repeatedly examine or tune against TEST.
6. Render's lightweight demo backend is **not** automatically the Chroma B3 implementation. A production/demo switch and corresponding evidence remain separate work.
