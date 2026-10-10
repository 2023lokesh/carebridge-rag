# CareBridge — Token-safe indexing and development retrieval results

**Executed:** October 10, 2026. **Source archive:** GitHub Actions run `38016315533` (163 CDC pages, 35 PDFs, 13 HTML table pages; 3,063 normalized source blocks). **Source snapshot SHA-256:** `226169a7bb7ad01ce1751f2a431b810df0e1fc7d006c9b64f29b755f4dc7f683`.

**Code:** [PR #9](https://github.com/2023lokesh/carebridge-rag/pull/9). **Actual index build:** [Actions run 38059975329](https://github.com/2023lokesh/carebridge-rag/actions/runs/38059975329) (successful). 

## Indexed source evidence

| Metric | Fixed-size 180/30 words | Heading-aware |
|---|---:|---:|
| Source pages | 163 | 163 |
| Source extraction blocks | 3,063 | 3,063 |
| Pre-token-cap distinct chunks | 3,262 | 3,021 |
| Chunks requiring extra tokenizer-budget splitting | 178 | 120 |
| Final MiniLM vectors | **3,477** | **3,301** |
| Remaining segments above 256 model tokens | **0** | **0** |
| Max actual embedding model tokens | **255** | **255** |
| Median / 95th percentile model tokens | 44 / 254 | 44 / 254 |
| Orphan/missing Chroma IDs | **0 / 0** | **0 / 0** |

Model: `sentence-transformers/all-MiniLM-L6-v2`, 384-dimensional embeddings, cosine distance, L2 normalization. Original CDC text was retained via fast-tokenizer character offsets; every Chroma ID was independently compared against the saved chunk manifest.

## Real baseline measurement: URL-labelled retrieval on frozen DEV only

Of 24 frozen development questions, **18 have source-URL gold labels** (five are unanswerable and one ambiguous/adversarial question does not specify a relevant URL). Only these 18 are scored for retrieval. All 16 sealed test questions remain untouched.

| Metric | B1 BM25 — fixed, corrected | Heading-aware BM25-only ablation |
|---|---:|---:|
| Recall@5 | 0.6944 | 0.7500 |
| Recall@20 | 0.9444 | 0.9444 |
| MRR | 0.5903 | 0.5912 |
| nDCG@10 | 0.6305 | 0.6317 |
| p50 retrieval-only latency (local CPU) | 70.17 ms | 69.76 ms |
| p95 retrieval-only latency (local CPU) | 122.07 ms | 125.29 ms |

Paired heading-minus-fixed Recall@5 improvement **+0.0556**, with a 95% bootstrap confidence interval **[0.0000, 0.1667]** (18 shared questions). Because zero lies in the interval, the improvement is **not established as statistically significant**. Recall@20 did not change. These are URL-level proxy relevance scores, not expert judgments of exact chunk relevance.

The uncapped fixed-index BM25 trial measured Recall@5 0.6944, Recall@20 0.9444, MRR 0.5894, and nDCG@10 0.6300. Comparing original to tokenizer-safe fixed chunks yields effectively unchanged retrieval quality; the fix eliminates silent truncation, not demonstrated recall degradation.

## Outstanding course requirements

1. **B2** actual neural dense retrieval scores for the 18 URL-labelled development questions using the corrected fixed index.
2. **B3** heading-aware BM25/neural RRF followed by actual cross-encoder reranking; measure added latency, candidate pool >=20, final top 5, and lift versus no rerank.
3. **B0** real closed-book generation experiment, plus generated answer correctness, source citation validity, refusal/over-refusal, per-answer cost, one-factor ablations, and a 15-question human-labelled failure taxonomy.
4. Obtain independent teammate approval evidence and document honest AI-assisted question-draft provenance.
5. Preserve and run **the 16 test questions exactly once** only after model and evaluation protocol are frozen.

The real private dev file (`dev_24.jsonl`) was not uploaded to GitHub; the evaluation script is shipped in PR #9 and requires the downloaded index archive. Running the **local** B2/B3 commands is specified in `docs/TOKEN_SAFE_NEURAL_EVALUATION.md`. No B2/B3 numbers are fabricated here.

**Action artifact retention:** save the full index ZIP before it expires seven days after the October 10 build.