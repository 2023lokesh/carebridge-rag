# 05 — Generated answers, citation diagnostics and human-review reconciliation

**Status: actual DEV generation completed, human-scoring QA remains open (October 10, 2026).** The evidence-backed [GitHub Actions run #38066174591](https://github.com/2023lokesh/carebridge-rag/actions/runs/38066174591) **succeeded** and produced **96 genuine generated responses** across **24 frozen development questions × 4 baselines**. Its artifact `carebridge-dev-generated-answers-38066174591` (ID **11675249068**, expiring **October 17, 2026**) contains sanitized `aggregate_automated.json` and private Fernet-encrypted answers. The run authenticated the 24-item DEV fingerprint and confirmed **zero sealed TEST questions were loaded**.

The same CPU-local **HuggingFaceTB/SmolLM2-360M-Instruct** model, greedy decoding and 96-new-token cap was used throughout. B0 had no retrieval, B1 used fixed BM25, B2 used fixed MiniLM neural, and B3 used heading-aware RRF + cross-encoder. Shared safety-screen rules applied identically to every baseline. The live Render demo uses a different, smaller corpus and is not this benchmark setup.

## Measured automated run metrics (all 24 DEV questions per baseline)

| Metric | B0 closed book | B1 BM25 | B2 neural | B3 hybrid+rerank |
| --- | ---: | ---: | ---: | ---: |
| Generated answers | 24 | 24 | 24 | 24 |
| Deterministic policy-blocked cases | 5 | 5 | 5 | 5 |
| Heuristic abstentions | 5 | 5 | 5 | 5 |
| Answers with valid `[S#]` reference markers | **0** | **0** | **1** | **0** |
| Invalid citation-reference IDs | 0 | 0 | 0 | 0 |
| p50 warm total latency (ms) | **2,657.53** | 4,913.15 | 4,618.47 | 5,972.53 |
| p95 warm total latency (ms) | 8,497.64 | 11,749.74 | 10,978.78 | 10,520.44 |
| Total model-generated tokens | 897 | 655 | 683 | 574 |

All numbers above are from the actual successful run, not human factual/citation scores. Total latency includes retriever (if applicable) plus model decoding, excludes cold model loading, infrastructure initialization, and network/UI effects. Short-circuited policy refusals consume no generation time. This is a small CPU model and these latency measurements should not be generalized to another deployed model.

**Important citation finding:** Out of the 54 answerable retrieval-grounded question/configuration outputs (18 labelled DEV questions × B1/B2/B3), **zero emitted a valid `[S#]` citation marker**. The only valid marker was produced on G40/B2 (a different adversarial/ambiguous case). A valid source marker by itself does not prove passage support. This citation-format failure is an observed system weakness, not a grader success.

## Team-scoring status and QA restriction

A team-updated private review sheet dated October 10 contains **96 reviewer-entered factual/safety/refusal/citation judgments** with reviewer names. The submitted sheet initially had no generated answers or cited URLs. The archived 96 real answers have now been reconciled by unique question/baseline ID into a **private evidence audit copy**, preserving the human scores. The audit flagged:
- **25** rows marked citation support=1 with **no actual cited marker**.
- **67** rows containing a zero score without a meaningful failure category.
- **33** answerable retrieval rows marked citation support=NA even though the answer lacks the required citation.
- **Four** G40 comments referring to a cafeteria menu rather than its personal-vaccine question.
- **Zero of 15** required separate manual error-analysis entries completed.

These issues overlap; **87/96 rows** require one or more second-pass checks. Because the input human labels conflict with mechanically verifiable outputs, **do not release a reviewed-accuracy, citation-support or clinically-safe claim until the team corrects and signs off on the restored evidence workbook**. Preserve the original reviewed sheet, actual answer evidence and audit trail privately. The public GitHub repository must contain none of the 24 questions, gold answers, generated answers, confidential secret or reviewer workbook.

See `docs/GENERATION_B0_B3_HUMAN_SCORING.md` for required per-answer standards and `scripts/score_human_review.py` for strict category and reviewer-field validation.

## Remaining work
Review all highlighted private rows against actual generated answer and CDC passage. Complete genuine error categories and at least 15 independently documented errors/failed-output analyses, then finalize human scores, paired confidence intervals and useful over-refusal/correct-refusal metrics. The 16 frozen TEST items are **still sealed**. Do not claim final held-out performance until the one-time approved test run.
