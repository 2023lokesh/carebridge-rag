# 03 — Student-authored golden questions and verification

**Status: 40 AI-suggested practice prompts prepared; independently student-authored/human-verified gold items: 0 evidenced.** These examples must **not** be submitted as the team's own human-authored golden set or treated as held-out labels.

`data/practice_question_ideas.jsonl` has exactly 15 single-hop, 6 multi-hop, 4 comparative, 4 temporal, 8 unanswerable, and 3 ambiguous/adversarial question ideas. The draft answers/source links are suggestions only. For the **distinct actual gold set**, team members must author questions from pages they have read, collect gold answers, valid source URLs, <=25-word directly copied evidence quotes, and actual search attempts for unanswerable items; record a real independent human verifier and timestamp for each. Multi-hop must cite >=2 different pages. The actual gold split must be 24 development / 16 untouched test, stratified 60/40 by the course's category quotas.

The instructor requires Friday authorship before testing the chatbot; since the prototype already existed before this work, **disclose the chronology and ask the instructor how to handle compliance**. Do not backdate timestamps or assert a never-run test score. `carebridge.benchmark.verify_item` and `stratified_split` reject practice rows.
