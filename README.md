# CareBridge — CDC-grounded vaccine education chatbot

**University of the Cumberlands MSAI 633 residency project · Updated October 10, 2026**

[Live educational demonstration](https://carebridge-vaccine-chatbot.onrender.com)

**Website experience (professor-requested refresh):** The homepage is now a standalone introduction to CareBridge, its CDC-linked educational role, how it works and medical-safety limits. A bottom-right **Ask CareBridge** floating chatbot opens a guided two-step topic/question wizard with free-text questions, linked CDC evidence and the existing `/api/chat` endpoint. Mobile and keyboard controls are supported. The public demo continues to use curated summaries/lexical retrieval, not the independently evaluated 163-page MiniLM/Chroma corpus. See [the web-widget guide](docs/WEB_WIDGET_GUIDE.md).
 · [GitHub repository](https://github.com/2023lokesh/carebridge-rag) · [Course submission status](docs/SUBMISSION_STATUS.md) · [Demo script](docs/DEMO_SCRIPT.md)

CareBridge is an **educational vaccine-reference prototype**, not a clinician, diagnosis engine, individualized vaccine recommendation system, or HIPAA-certified healthcare product. Do not enter protected health information or patient identifiers. A cited URL is not by itself proof that the text supports a specific medical claim or reflects the latest CDC guidance.

## Two intentionally distinct configurations

| Component | Public Render demo | Measured research/evaluation pipeline |
| --- | --- | --- |
| Data | Small curated vaccine summaries linked to CDC | **163 distinct archived normalized public CDC pages**, including 35 PDFs, 13 table-bearing HTML pages |
| Retrieval | Local BM25 / TF-IDF proxy / hybrid and lightweight postscore | Real BM25, 384-dimensional MiniLM dense Chroma cosine, RRF, cross-encoder |
| Chunking | Bundled demo blocks | **3,477 fixed** / **3,301 heading-aware**, tokenizer safe, zero orphans |
| Inference | Deterministic demo reply; optional OpenAI if configured | Controlled same CPU-local SmolLM2-360M-Instruct planned for B0–B3 generation |
| Evaluation | Smoke/demo tests, **not** graded metrics | Verified real retrieval-only DEV run #38062665587; generation implementation in PR #14 awaiting merge/run |

**The deployed public demo does not currently query the 163-page Chroma index.** Distinguish the demo from the indexed experiment in any presentation.

## Quick start: educational demo

Use Python 3.11 or later:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
# Browse http://127.0.0.1:8000
```

Run tests:

```bash
python -m pip install pytest httpx 'cryptography>=43,<50'
python -m pytest -q
```

Endpoints: `GET /`, `GET /healthz`, and `POST /api/chat` with `{"question":"What is MMR?","mode":"hybrid","history":[]}`. The response has `answer`, `refused`, `sources`, `trace`, and `stats` where supported. The app provides clickable citations, history, explicit refusals, a visible retrieval trace and medical high-stakes referral. See `app.py`, `carebridge/rag.py`, `carebridge/safety.py` and `static/index.html`.

## Ethical real CDC corpus and indexes

The real crawl was performed through [GitHub Actions run #38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533), not simulated. Result: **165 raw pages, 163 normalized pages, 35 PDFs, 13 table-containing HTML pages, 3,063 normalized blocks, no crawl errors or raw hash mismatches**. The crawler obeys robots.txt, descriptive User-Agent, ≥1 second between requests, CDC HTTPS allowlists, and excludes patient/staff/directory/login content. Raw evidence is retained in the external Actions artifact and locally by the team, not committed as bulk data to this repo.

From the saved archived normalized `data/normalized.jsonl`, the separate fixed and heading-aware MiniLM/Chroma indexes were built successfully by [Actions run #38059975329](https://github.com/2023lokesh/carebridge-rag/actions/runs/38059975329), producing **3,477** and **3,301** tokenizer-safe chunks respectively, with zero missing or orphan IDs. Each MiniLM vector has 384 dimensions, normalized for cosine distance. The indexes must be downloaded from the corresponding artifact; they are **not** part of the lightweight public demo deployment. Source and instructions: `carebridge/index.py`, `carebridge/token_budget.py`, `scripts/verify_comparison_indexes.py`, and `docs/TOKEN_SAFE_NEURAL_EVALUATION.md`.

## Frozen golden set and observed DEV retrieval metrics

The team has attested individual review of the 40-question dataset. Its category distribution is **15 single-hop / 6 multi-hop / 4 comparative / 4 temporal / 8 unanswerable / 3 ambiguous**. The **24 DEV / 16 sealed TEST** stratified split uses random seed 633 and recorded fingerprints. The original question candidates were **AI-assisted**, subsequently self-reviewed by assigned team members on October 10; **independent student authorship before chatbot development has not been established**. Do not claim Friday-before-system authorship; follow instructor instructions for academic-integrity disclosure. See `reports/03_golden_set.md`.

A **real successful retrieval-only** [DEV evaluation run #38062665587](https://github.com/2023lokesh/carebridge-rag/actions/runs/38062665587) authenticated **24 development records, 0 TEST records** and evaluated the **18 source-URL-labelled** DEV questions. Unanswerable/ambiguous cases need refusal evaluation, not bogus retrieval success.

| Metric | B1 BM25 fixed | B2 MiniLM fixed | B3 heading hybrid + cross-encoder |
| --- | ---: | ---: | ---: |
| Recall@5 | 0.6944 | 0.8056 | **0.8889** |
| Recall@20 | 0.9444 | **1.0000** | **1.0000** |
| MRR | 0.5903 | **0.7469** | 0.7231 |
| nDCG@10 | 0.6305 | **0.7757** | 0.7463 |
| p50 warm retrieval (ms) | 88.59 | **14.93** | 928.93 |
| p95 warm retrieval (ms) | 93.09 | **17.96** | 988.44 |

This is **source-URL-level retrieval relevance**, not human-confirmed passage entailment or generated-answer correctness. Latencies exclude model startup and generation, and B1 recomputes lexical tokenization per query. All nonzero Recall@5 paired bootstrap intervals include zero. See [retrieval and reranking report](reports/04_retrieval_reranking.md) and [full performance limitations](reports/06_final_performance.md).

## B0–B3 generation and human scoring: implementation prepared

[PR #14](https://github.com/2023lokesh/carebridge-rag/pull/14) adds the **DEV-only** four-baseline generated-answer workflow (`.github/workflows/evaluate-generation-dev.yml`), `scripts/eval_generation_dev.py`, private decryption and human-review scoring tools, and regression safety tests. The model is the **same SmolLM2-360M-Instruct CPU-local instruct generator** for all four baselines; retrieval and reranking are varied in controlled conditions. Runs use **24 DEV questions × 4 baselines = 96 generated answers**; the 16 TEST questions remain sealed.

**Do not quote B0 scores, generated-answer accuracy, citation support, refusal quality, clinical safety, or end-to-end latency until a successful workflow and independent human scoring actually exist.** The Actions artifact will contain only sanitized automated output and **Fernet-encrypted** questions/answers. Human reviewers locally decrypt with the existing DEV secret, review every answer and actual CDC passage, record reviewer identities/dates and genuine failure categories, then compute paired accuracy CIs. The course requires at least 15 real manually categorized errors; none are fabricated in this repo.

Protocol: [docs/GENERATION_B0_B3_HUMAN_SCORING.md](docs/GENERATION_B0_B3_HUMAN_SCORING.md).

## Reports, collaboration and academic integrity

- [`reports/00_proposal.md`](reports/00_proposal.md) — problem, source, architecture and plan.
- [`reports/01_ingestion.md`](reports/01_ingestion.md) — actual CDC acquisition and audit.
- [`reports/02_chunking.md`](reports/02_chunking.md) — measured chunking/re-index and controlled BM25 ablation.
- [`reports/03_golden_set.md`](reports/03_golden_set.md) — frozen categories, review attestation and original AI-assisted provenance.
- [`reports/04_retrieval_reranking.md`](reports/04_retrieval_reranking.md) — actual B1/B2/B3 retrieval metrics, one-factor reranker test and paired 95% CIs.
- [`reports/05_generation.md`](reports/05_generation.md) — genuine generator protocol and unmeasured accuracy/safety requirements.
- [`reports/06_final_performance.md`](reports/06_final_performance.md) — what was actually measured, omissions and reproducibility.
- [`reports/07_ethics.md`](reports/07_ethics.md) — crawl etiquette, PII avoidance, refusals, prompt injection, staleness and limits.

Collaboration should use feature branches, **actual separate teammate approvals**, recorded individual commits and GitHub Issues/Projects. Existing PRs and tests do not substitute for missing formal approval evidence. `main` branch protection enforcement must be verified by an administrator. Never publish `.env`, protected information, the secret, private golden content, raw user messages or decrypted response review CSV.

**AI-use disclosure:** AI-assisted code, draft questions, documentation and technical guidance were used in this project. The team reviewed source accuracy and must be able to explain all evaluation formulas and data/ethics decisions. The instructor requires student authorship of golden questions before the chatbot existed; the team's disclosed chronology differs from that rule and requires an instructor-approved determination, not invented dates.

## Known limitations

Clinical accuracy, hallucination rate, citation entailment, generated-answer/refusal rates, prompt-injection resistance under live LLM generation, staleness display, 15-case failure adjudication, private final 16-item TEST run, and full deployed 163-page index integration are **not yet verified complete**. B3 changes multiple factors versus B2; only its within-candidate reranker ablation is one-factor. GitHub artifacts have short retention; download evidence before **October 17, 2026**.