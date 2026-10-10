# CareBridge MSAI 633 — five-person ownership plan

This is a proposed split for the team to confirm. GitHub usernames are unknown, so no issue assignment or teammate review is claimed. Each person should contribute code to **more than one** pipeline stage and independently review another person's pull request.

| Person | Role | Primary course deliverable | Cross-stage contribution/review |
| --- | --- | --- | --- |
| Baroowah, Lakhyajyoti | Product Manager | Define scope, 40-item human-authored question inventory, source review schedule, maintain issue statuses and ethics coordination | Verify citations/questions and review UX/refusal PR |
| Asha Kiran Narla | Full Stack Developer | Chat history, visible retrieval scores and citations, refusal UX, live demo, generation report | Review safety/evaluation PR and test API |
| Deepaksai Pasupuleti | Lead Engineer | Architecture, two chunking approaches, zero-orphan reindex migration, code quality, CI and PR review rules | Review crawler/index PR and performance analysis |
| Munagala, Lokesh Sai Krishna | Data Engineer | Ethical CDC crawler, raw SHA-256 archive, PDF/table extraction, 150-page audit | Review embedding/index code and contribute gold-source checks |
| Karthik Lakamraju | Data Engineer | Embedding model, Chroma, BM25/TF-IDF/neural hybrid, actual cross-encoder, evaluation metrics | Review ingestion code and statistical scoring |

## Shared review and integrity tasks

- For **every student-authored gold item**, log who authored it, when, which original page was read, the direct <=25-word quote, a separate verifier, and whether it is answerable. Authors and reviewers must independently examine the page; AI examples in `data/practice_question_ideas.jsonl` are suggestions **only**.
- The chatbot already existed before the gold set. **Do not backdate** authorship to Friday; report chronology honestly and get instructor guidance.
- Use the 24/16 category-stratified development/test split only after 40 legitimate items are frozen. Do not look at the holdout until the one-time final evaluation.
- An admin must enable `main` protection and require a separate teammate's PR approval before **this or later PRs** merge.
- Each student should demonstrate and explain another stage besides their primary stage during the course's live Q&A.
- Assign [Issues #1–#5](https://github.com/2023lokesh/carebridge-rag/issues) after confirming each member's GitHub username.
