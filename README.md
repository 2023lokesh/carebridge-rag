# CareBridge — CDC-grounded vaccine education chatbot

**Status:** runnable **educational prototype**, not a clinical decision-support tool. The public-facing demo is backed by a small, manually curated set of summaries linked to CDC pages; it is **not** the completed 150-page graded corpus. Do not enter patient data, personal health history or identifiers.

CareBridge is a FastAPI app with a responsive chat page, source URLs, history-aware follow-ups, visible retrieval trace (pre/post ranking scores), explicit refusals, and emergency referral messaging. It needs **no API key** in its default demo mode.

## Quick start (Python 3.11 recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Verify **http://127.0.0.1:8000/healthz**. For automated tests:

```bash
python -m pip install pytest httpx
python -m pytest -q
```

For a running-server health/chat check, use `python scripts/smoke_test.py --url http://127.0.0.1:8000`.

### What it does today

- **UI:** browser chat, clickable references, short-term follow-up handling, expandable retrieval trace, BM25 / hybrid / TF-IDF comparison.
- **Default retrieval:** locally ranked BM25 + TF-IDF (non-neural proxy) with reciprocal-rank fusion; a 20-candidate pool (where at least 20 chunks exist); an explicitly named lightweight proxy post-score. The default demo does **not** claim to have neural embeddings or a cross-encoder reranker.
- **Refusal:** personal clinical questions, emergencies, unsupported topics, and insufficient matching evidence. The citations are links to referenced CDC pages; the included summaries are not live CDC downloads.
- **Optional generation:** enable only after installing `openai` and setting `OPENAI_API_KEY` and `CAREBRIDGE_GENERATION=openai`. The default answer generation is deterministic/extractive and free of third-party API calls.
- **Not yet done:** actual 150-page crawl, ≥5 downloaded PDFs, ≥3 ingested table pages, human-verified 40-item golden set, dev/test evaluation, full-system benchmark, and hosted live deployment. Do not present these as completed for the course.

## Production-ish deployment to Render (after your own GitHub repo exists)

1. Create a **new** empty GitHub repository, ideally `carebridge-rag`, rather than reusing an unrelated project.
2. Copy this whole directory into the new repo root. From this directory run:

   ```bash
   git init
   git checkout -b main
   git add .
   git commit -m "feat: add CareBridge educational chatbot"
   git remote add origin https://github.com/YOUR_USERNAME/carebridge-rag.git
   git push -u origin main
   ```

3. In [Render Dashboard](https://dashboard.render.com/), choose **New → Blueprint** and select this GitHub repository. The included `render.yaml` creates the `carebridge-vaccine-chatbot` free Python web service with build command `pip install -r requirements.txt`, start command `uvicorn app:app --host 0.0.0.0 --port $PORT`, and health check `/healthz`.
4. After the build is **Live**, use the URL Render displays, then test `https://YOUR-SERVICE.onrender.com/healthz`. Do not guess the subdomain before deployment succeeds.
5. On free plans, the service may sleep between visits. **Do not add** `OPENAI_API_KEY` for the public classroom demo; use the bundled local demo to avoid cost and inadvertent disclosure of patient questions.

**GitHub course workflow:** In repository settings protect `main`, require 1 PR approval (when team review is available), turn on Issues, use short-lived branches, and create issues for crawl, extraction, indexing, evaluation, ethics, and documentation. Never commit `.env`, tokens, or raw private data.

## Full graded RAG pipeline: optional, not shipped as deployed demo

The modules below are implemented as an **experimental workflow** but require separate corpus collection and model installation; these commands have not been benchmarked against a complete corpus.

```bash
python -m pip install -r requirements-full.txt
python -m carebridge.crawler --contact your-valid-email@example.edu --max-pages 150
python -m carebridge.extract --manifest data/raw/manifest.jsonl --output data/normalized.jsonl
python -m carebridge.index --corpus data/normalized.jsonl --strategy fixed
python -m carebridge.index --corpus data/normalized.jsonl --strategy heading
# Each rebuild deletes old chunks then verifies the active IDs, without re-crawling.
# To run the indexed corpus locally, set CAREBRIDGE_BACKEND=full after preparing the index.
```

**Warning:** the crawler checks `robots.txt` with a descriptive `User-Agent`, allows at most one request per second, only follows CDC vaccine/IIS HTTPS URLs, refuses redirects off-site, stores raw bytes before parsing, and excludes directory/login pages and identifiable contact details. A real contact email is required. Inspect site permissions and the saved manifest, including final distinct URLs/PDFs/tables, before submission. Some pages may disallow crawling; do not bypass restrictions. Raw data and persistent indexes are gitignored.

**Two chunk strategies:** fixed 450-token word windows with 75 overlap, and heading-sensitive windowing. Chunk IDs deterministically hash the document, strategy, local index, and text. The Chroma index uses SentenceTransformer `all-MiniLM-L6-v2` (384 dimensions, normalized embeddings, cosine metric), plus lexical BM25 and optional `cross-encoder/ms-marco-MiniLM-L-6-v2` reranking. See `carebridge/index.py`, `carebridge/full_backend.py`. Chroma runs locally and is not provisioned on a free Render server by default; an ephemeral file system is unsuitable for a persistent 150-page index unless rebuilt from committed public normalized data at deploy time or moved to durable storage.

## Evaluation and coursework

A **real** 40-question golden set must be authored from sources, human-verified and split once 60/40 by category (15 single-hop, 6 multi-hop, 4 comparative, 4 temporal, 8 unanswerable, 3 ambiguous/adversarial). `carebridge/evaluate.py` enforces human verification and creates reproducible splits, with retrieval metrics. Further grading requires actual B0 (no retrieval), B1 (BM25), B2 (neural dense + naive chunks), and B3 (final hybrid/reranker) runs, answer/citation/refusal checks, latency/cost, confidence intervals, error-label review, and an honest Sunday report. The presence of code is **not** evidence of a measured score.

Proposal: `reports/00_proposal.md`. See the instructions in the uploaded MSAI 633 project brief for additional grading criteria.

## API

- `GET /` — responsive chat UI
- `GET /healthz` — health and active mode
- `POST /api/chat` — `{ "question": "What does MMR protect against?", "mode": "hybrid", "history": [] }`; returns `answer`, `refused`, `sources`, `trace`, `stats`.

No authentication is included: this is **not suitable for real clinical deployments**. Do not submit patient identifiers, symptoms, or health history. No request text is intentionally persisted; Render and other hosting providers may log metadata, and optional LLM requests would be processed by the configured model provider. No HIPAA or medical compliance claim is made.

## Medical safety and ethics

This project is **educational**, not intended to diagnose, triage, treat, prescribe, recommend vaccination for an individual, or replace a clinician. An emergency query shows a 911/local-emergency-number referral; personal clinical questions trigger referral, not an individualized answer. Retrieved webpages are untrusted data; obvious injection phrases and contact details are excluded. The latest policy and clinician recommendations must be checked at the CDC source because medical guidance can change. Citation URL presence alone does not prove sentence-level factual verification.

**AI-use note:** Portions of the source code, documentation, and the manually curated demo explanations were drafted with an AI assistant. Team members must inspect source accuracy, review logic, independently author and verify the golden set, and disclose AI usage under the project rubric.

## File map

```text
app.py                     FastAPI server and API
static/index.html          Browser chatbot UI
carebridge/rag.py          Lightweight retrieval and response path
carebridge/safety.py       Safety, URL, prompt-injection checks
carebridge/crawler.py      Ethical public CDC crawler
carebridge/extract.py      HTML and PDF content extraction
carebridge/corpus.py       Normalization, deterministic IDs and chunking
carebridge/index.py        Optional neural Chroma indexing/re-chunk
carebridge/full_backend.py Optional dense + BM25 + cross-encoder retrieval
carebridge/evaluate.py     Golden-set constraints, metrics/split
carebridge/generate.py     Optional cited OpenAI generation
render.yaml                Render Blueprint
Dockerfile                 Alternate container deployment
scripts/smoke_test.py      Running-service smoke test
.github/workflows/tests.yml GitHub Actions test workflow
tests/                     Automated tests
```


## MSAI 633 evaluation-workflow update

The feature branch includes a [graded-workflow runbook](docs/EVALUATION_RUNBOOK.md), a [crawl audit](carebridge/audit.py), a [40-question AI-generated *practice* set](data/practice_question_ideas.jsonl), [branch-protection setup instructions](docs/BRANCH_PROTECTION.md), and honest, unexecuted report templates. Practice examples are **not** independently human-verified gold items. The full 150-document CDC crawl and B0–B3 scoring still require actual execution and team verification. This project currently runs a small prototype on Render; it is not a clinical decision-support system.
