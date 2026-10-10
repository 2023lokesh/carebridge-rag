# 01 — Crawl, extraction and inventory (execution not completed)

**Status: Not graded-ready.** The source archive does not yet exist in this repository; no numeric successes are claimed.

Run `.github/workflows/crawl.yml` with an approved contact email and inspect its artifact `data/raw/manifest.jsonl`, normalized JSONL, and `reports/01_ingestion_metrics.json`. That machine-computed file counts **distinct successfully stored AND normalized public URLs**, not candidate links, chunk counts, or queue entries. The verifier rereads saved bytes, checks SHA-256 and checks ≥150 URLs including ≥5 distinct PDF URLs and ≥3 distinct HTML table pages. A failed threshold causes a nonzero exit and must remain visible.

Actual measured unique page count: **not collected**. Actual measured PDF count: **not collected**. Actual measured table-page count: **not collected**.

Seeds include CDC VIS PDFs and CDC immunization schedule table pages; these are candidates **only**. PDFs must yield searchable text and tables must survive extraction. After a real run, inspect which sources were skipped, demonstrate robots/1 request/sec with logs, and record the fetched effective dates. The archived bytes are omitted from Git because they may be large; retain the Actions artifact or another approved storage location as part of course evidence.
