# CareBridge website refresh — landing page with floating chatbot wizard

**Professor feedback addressed:** CareBridge's public homepage must be an actual informational website. Chat functionality should be separate from the webpage itself, presented as a friendly wizard-style assistant in a floating chat widget.

## Interface

- Informational page: hero, plain-language **What is CareBridge?**, project metrics, **How it works**, educational safety boundaries and FAQs, external project/CDC links.
- Persistent bottom-right **Ask CareBridge** launcher. The conversation only opens on a click and can be closed via button or Escape. It does **not** dominate the page on initial load.
- Wizard Step 1: choose a general vaccine topic. Step 2: choose a suggested question, or enter an original question at any time. After each answer the user can restart the topic wizard.
- Real demo connectivity preserved: `POST /api/chat` with `{question, mode, history}`. Displays the returned answer, CDC source links, disclaimer and optional expandable retrieval details without using unsanitized HTML.
- Accessible labeled controls, keyboard navigation and Escape-to-close; full-screen widget on mobile, `prefers-reduced-motion` support.
- The existing FastAPI API and demo backend are unchanged; **this is a frontend redesign, not a switch to the research-only Chroma model**.

## Important accuracy disclosures

The live Render instance still uses a small collection of curated CDC-linked summaries and lexical/TF-IDF proxy retrieval. Separate experiments crawled 163 CDC pages, compared 3,477 fixed versus 3,301 heading-aware chunks and measured neural retrieval and CPU-local generation. These research experiments are not yet the same runtime as the live public web application. This distinction is included on the website itself.

## How to test before deployment

```bash
python -m pip install -r requirements.txt pytest httpx 'cryptography>=43,<50'
python -m pytest -q
python -m uvicorn app:app --reload
```

Open http://127.0.0.1:8000. Ensure the landing page appears with no open chat. Click the floating wizard, select **MMR & other vaccines**, choose **What does the MMR vaccine protect against?**, verify an answer and CDC sources. Close and reopen the widget, and test on a narrow mobile viewport. A separate offline Playwright test verified the question and answer flow with a mocked `/api/chat` response; it does not replace a live deployed backend smoke test.

## Deployment

Once a separate teammate reviews and merges the UI PR into `main`, Render should deploy the updated `static/index.html` with the normal service build/deploy process. No new credentials, frontend dependencies or cloud services are required. Verify the deployed service through its URL and confirm `/healthz` and `/api/chat` respond as before.
