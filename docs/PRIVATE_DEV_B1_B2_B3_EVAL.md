# Actual B1/B2/B3 development-only evaluation

The fixed and heading-aware MiniLM/Chroma indexes are already built. GitHub Actions
`evaluate-neural-dev.yml` compares them without rebuilding or re-crawling, using
**only** the frozen 24-item development data from October 10, 2026.

## Required encrypted input

1. Locally encode the **DEV-ONLY** `dev_24.jsonl` from the private golden-set ZIP:
   `python -c "import base64,gzip,pathlib;print(base64.b64encode(gzip.compress(pathlib.Path('dev_24.jsonl').read_bytes())).decode())"`
2. GitHub repository Settings → Secrets and variables → Actions → New repository secret.
   Name: `CAREBRIDGE_DEV_GOLD_GZIP_B64`. Paste the one-line base64 value and save.
   **Do not upload the full 40-item gold or the sealed 16-item test questions!**
3. GitHub Actions → `Evaluate real CDC B1 B2 B3 (private DEV only)` → Run workflow on main.
   Use `index_run_id = 38059975329` while the Oct 10 index-build artifact remains
   available (7-day retention ending roughly Oct 17). If expired, rebuild indexes first.
4. Download `carebridge-development-retrieval-<runid>` artifact and review four JSON outputs.
   It contains aggregate scores, paired bootstrap CIs and per-ID metrics. It does **not**
   contain question text or answer labels.
5. Document results in `reports/04_retrieval_reranking.md` only after verifying the real run.
   Do not score the sealed 16 test questions until all development decisions are frozen.

## Evaluation validity and limitations

- B1: BM25, fixed/token-safe; B2: dense MiniLM Chroma, **identical fixed chunks**;
  B3: heading-aware BM25 + dense RRF, then a genuine cross-encoder reranking the
  top 20 candidates. The report also computes the same B3 retrieval *before*
  reranking: this is a one-factor estimate of reranker lift on the same candidate pool.
- 18 development questions have source-URL relevance labels; 6 unanswerable/other
  items are excluded from the retrieval metrics and need separate refusal scoring.
- Every comparison uses same 18 labelled questions, with Recall@5/20, MRR,
  nDCG@10, p50/p95 warm-query latency, and bootstrap 95% paired intervals.
- Report is **retrieval only**: it is not B0, generated-answer correctness,
  citation validity, abstention quality, model-token cost, or test-set performance.
- Original golden question ideas were AI-assisted; team attested individual self
  review. The record does not establish independently student-authored origins.
- The workflow refuses any mismatched SHA-256, unexpected question IDs,
  duplicate IDs, changed category proportions, or overlap with sealed test IDs.
- Use one locked, course-approved final evaluation of the untouched 16 questions
  only after development decisions are complete.
