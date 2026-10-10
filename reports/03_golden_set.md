# 03 — Golden evaluation data and test isolation

**Observed October 10, 2026:** 40 question rows; assigned team members attest they individually checked every answer and source. The original question ideas were AI-assisted. Reviewers are the assigned team members (individual *self-review*, not a separate independent person); records have October 10 verification dates. Instructor-required independent student authorship *before Friday chatbot construction* is not evidenced; disclose actual timeline and seek a ruling, never backdate.

| Category | Total | DEV | TEST (sealed) |
| --- | ---: | ---: | ---: |
| Single-hop | 15 | 9 | 6 |
| Multi-hop | 6 | 4 | 2 |
| Comparative | 4 | 2 | 2 |
| Temporal | 4 | 2 | 2 |
| Unanswerable | 8 | 5 | 3 |
| Ambiguous/adversarial | 3 | 2 | 1 |
| **Total** | **40** | **24** | **16** |

The deterministic stratified freeze uses seed **633** and dev payload SHA-256 `012677aa7a605316f2b0f5f9712b64d0b0c9deb3bd6f151b531e16ceededc6bf`. Public `data/frozen_split_manifest.json` includes category counts and IDs, *not private questions or answers*. Actual evaluation workflow [#38062665587](https://github.com/2023lokesh/carebridge-rag/actions/runs/38062665587) authenticated 24 DEV, loaded **0 TEST**, and measured source-URL retrieval on 18 answerable DEV cases. The six remaining DEV items require human-reviewed refusal/ambiguity scoring, not assigned artificial retrieval accuracy. The 16 TEST items remain unexamined for scoring.

Original verified worksheet and DEV/TEST content are preserved privately with CDC URLs, evidence excerpts and individual team review attestation. Full golden-set provenance should be supplied privately only to the instructor via authorized delivery. Gold origin is AI-assisted draft + team self-review, not proven independently student-authored.
