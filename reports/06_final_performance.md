# 06 — Final performance and reproducibility

**Status: no graded B0–B3 scores yet.** A real 40-item human-verified gold set, full corpus, and valid closed-book LLM baseline do not yet exist. The current exploratory 29-question candidate-URL diagnostics are not suitable for final scoring.

Before reporting any numeric score: run B0 closed-book with a real LLM; B1 BM25, B2 neural dense fixed, B3 reranked hybrid structure-aware; report B0-correct versus B0-incorrect subset; list Recall@5/20, MRR, nDCG@10, factual answer correctness, citation validity, correct-refusal/over-refusal, p50/p95 end-to-end latency, monetary cost. Ablate one change at a time. Compute uncertainty (95% paired bootstrap or McNemar) and manually categorize >=15 actual errors with evidence. Run the frozen **40% holdout once** after all dev tuning.

Record actual contributors, pull requests, approvals, conflict resolutions, model/config versions, and every executed command. Never represent AI-suggested practice metrics as held-out results.
