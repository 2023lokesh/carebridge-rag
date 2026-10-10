# 02 — Chunking and re-chunk migration

**Status: code prepared, unmeasured on required CDC corpus.** The fixed strategy uses 450 word-based tokens, overlap 75. The structure-aware strategy splits at headings and preserves source heading metadata. The full Chroma index builder stores normalized L2 embeddings, cosine metric and a deterministic chunk ID; it builds a new version from saved normalized data, checks expected/actual IDs, atomically switches active collection, then deletes the old index version. This is not evidence that the graded re-chunk experiment has run.

To obtain real numbers, install optional dependencies, run both strategies from one raw/archive snapshot, capture `chunk_stats`, distribution by real model-token length, complete index IDs and orphan checks, retrieval metrics on the *same development set*, and the paired delta with 95% confidence interval. Commit observed measurements only after execution.
