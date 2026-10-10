# 07 — Ethics, safeguards and known risks

**Scope:** educational vaccine reference, **not clinical advice, triage, diagnosis or HIPAA-certified care**.

### Evidenced safeguard 1 — ethical public ingestion
The crawler parses robots.txt, uses an approved descriptive user-agent, waits at least one second between requests, restricts navigation to CDC vaccine/IIS HTTPS URLs and excludes login/directory/patient-contact paths. Real crawl [run #38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533): 165 raw public pages, 163 normalized, 35 PDFs, 13 table-bearing HTML pages, zero raw hash mismatches and no reported crawl errors. Do not add scraped private data or bypass site policy.

### Evidenced safeguard 2 — rule-based clinical/privacy refusals
Safety rules refuse or refer private records, personal identifiers, individualized vaccine decisions, emergency symptoms, prescribing requests and obvious instruction-override attacks; source citation URLs are CDC allowlisted. A genuine DEV local regression found **two false refusals** of general polio and varicella vaccine questions; [approved/merged PR #14](https://github.com/2023lokesh/carebridge-rag/pull/14) extends the topical vocabulary so general education is not blindly blocked. The post-fix 24-question DEV pre-generation screen refused 5 examples versus 7 before, **not a validated clinical/LLM refusal rate**.

### Risks and checks to finish
- **Citation support:** CDC URL or syntactically correct source marker does not prove the exact generated claim; 96 true human judgments remain pending after actual B0–B3 generated answers.
- **Staleness:** the archived CDC snapshot can lag current guidance; demonstrate visible source timestamps and consult current clinical guidance.
- **Prompt injection:** retrieved page text is untrusted. Detection code/tests exist but a captured live successful injection-resistance transcript is not yet documented.
- **Privacy:** prevent PHI, medical histories, emails or identifiable records entering the public demo, repo or Actions logs. The DEV questions and generated private answers are excluded from public GitHub, with a secret-derived encrypted review artifact.
- **Academic integrity:** original golden question ideas were AI-assisted and reviewed by assigned team members October 10 (self-review). This does not prove independent Friday student authorship; disclose the actual chronology.
- **Split integrity:** hash-frozen 24 DEV and 16 sealed TEST; [DEV run #38062665587](https://github.com/2023lokesh/carebridge-rag/actions/runs/38062665587) authenticated 24/0. Never evaluate TEST before final protocol freeze.
- **Hosted equivalence:** live Render demo uses a smaller example corpus, not the measured Chroma 163-page index. Do not overstate end-to-end deployment.

The real-crawl evidence and branch tests support two implemented safeguards, **not** proof of perfect medical accuracy or policy compliance. Report all unexecuted and unverified outcomes candidly.
