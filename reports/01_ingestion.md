# 01 — CDC crawl, extraction and inventory (measured evidence)

**Completed:** October 10, 2026, 02:19 UTC (October 9, 2026, 9:19 PM US Central).

**Workflow:** [GitHub Actions run #38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533) (`Collect and audit public CDC corpus`, success). **Artifact:** `cdc-crawl-evidence-38016315533` (artifact ID 11655982704; 5,742,085 bytes).

**Verdict: ingestion thresholds PASSED, according to the saved inventory and an independent SHA-256 verification of the downloaded raw archive.** These are observations from actual collected source documents, not estimates or candidate URL counts.

| Assignment criterion | Actual | Minimum | Result |
| --- | ---: | ---: | --- |
| Distinct successfully archived and normalized public source pages | **163** | 150 | PASS |
| Distinct successfully normalized PDF documents | **35** | 5 | PASS |
| Distinct HTML source pages containing extracted tables | **13** | 3 | PASS |
| Total downloaded public source URLs | 165 | — | Recorded |
| Extracted normalized content blocks | 3,063 | — | Recorded |
| SHA-256 mismatches or missing raw files | **0** | 0 | PASS |

**Content type breakdown:** 130 HTML downloads and 35 PDF downloads. Two archived HTML pages lacked a normalized record and were excluded from the 163-page threshold: `https://www.cdc.gov/iis/resources-refs/index.html` and `https://www.cdc.gov/vaccines/hcp/by-disease/dengue.html`. The normalized corpus contains 22 table-type blocks from 13 source pages. Spot inspection of the CDC VIS URL table showed column headings and pipe-delimited rows, but a complete table-preservation and date-quality audit remains to be done.

The automated audit reported `meets_assignment_minima: true`, with `errors: []`. An independent validation read all 165 raw files from the downloadable ZIP and recomputed their SHA-256 hashes: zero mismatches. Counts refer to distinct source URLs, not chunks or link candidates.

## Reproduction and preservation

1. Open the [successful GitHub Actions run](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533). Download the `cdc-crawl-evidence-38016315533` artifact under **Artifacts**.
2. It contains `data/raw/manifest.jsonl`, all archived `data/raw/*.bin` files, `data/normalized.jsonl`, and `reports/01_ingestion_metrics.json`.
3. **Important:** the artifact is scheduled to expire **October 17, 2026**. Save the raw and normalized evidence in an approved team-controlled location; the metrics JSON alone cannot reproduce the retrieval benchmarks.
4. Unzip into the repository root. Re-run `python -m carebridge.audit --manifest data/raw/manifest.jsonl --normalized data/normalized.jsonl --output reports/01_ingestion_metrics.json --require-thresholds`. Cross-check the result against the archived JSON and source manifests.

## Unfinished evaluations

- Review extracted PDF text, intact table structures, relevant effective dates and content staleness with human QA; do not claim every table was manually checked.
- Using the **saved** normalized corpus, produce both fixed-overlap and heading-aware chunk indexes, demonstrate deletion of stale chunks and no orphans, and log measured token-length distributions.
- Students must independently author and verify 40 gold questions against actual source pages. The AI-suggested 40-question practice draft is **not** a human-authored golden set; disclose the real chronology rather than claiming Friday-before-chatbot authorship.
- Evaluate true B0–B3 configurations, reranker lift and Recall@20, confidence intervals, answer correctness, citation validity, correct refusal, over-refusal, latency and cost, and hand-label ≥15 failures; report only observed metrics.
- The hosted chatbot still defaults to its small demo corpus. Completing this crawl does **not** automatically ingest the 163-source corpus into its live retrieval index.

**Academic-integrity note:** This report verifies corpus ingestion thresholds only, not full project compliance, full clinical validity, or measured neural retrieval performance.