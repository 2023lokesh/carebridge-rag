# CareBridge MSAI 633 — evidence-based submission checklist

**Updated October 10, 2026.** Cite only verified runs, not prepared code as completed experiments.

| Milestone | Evidence/status |
| --- | --- |
| CDC corpus | **163 normalized public pages, 35 PDFs, 13 table HTML pages**, [crawl #38016315533](https://github.com/2023lokesh/carebridge-rag/actions/runs/38016315533) |
| Token-safe indexes | **3,477 fixed, 3,301 heading-aware**, no orphans/overlimit, [build #38059975329](https://github.com/2023lokesh/carebridge-rag/actions/runs/38059975329) |
| Golden evaluation | **40** team self-reviewed originally AI-assisted question ideas, frozen **24 DEV / 16 sealed TEST**, seed 633 |
| Real retrieval evaluation | [B1/B2/B3 run #38062665587](https://github.com/2023lokesh/carebridge-rag/actions/runs/38062665587), 18 URL-labelled DEV queries; 0 TEST |
| B0–B3 generation code | [PR #14](https://github.com/2023lokesh/carebridge-rag/pull/14) **formally approved by ashakiran412, merged, CI passed** |
| Actual 96-answer generation | **Not yet run**: [GitHub workflow](https://github.com/2023lokesh/carebridge-rag/actions/workflows/evaluate-generation-dev.yml), index run ID `38059975329` |
| Human factual/citation/refusal/clinical judgments | **Pending** 96 actual reviewed answers, names/dates/evidence |
| 15 actual failure cases | **Pending** genuine failure classification |
| Final 16 TEST | **SEALED**, not scored |
| Public demo | Small example corpus, not full neural indexed backend |

**Next authorized step:** in GitHub Actions manually dispatch `Evaluate B0 B1 B2 B3 generated answers (private DEV only)` on `main` with index artifact run ID `38059975329`, before October 17. Verify actual success, download the encrypted response artifact, then use `scripts/review_generation_dev.py` on a trusted team machine. All **96 answers** must be manually adjudicated before publishing correctness/refusal/citation rates. Finally freeze the configuration before one controlled 16-TEST evaluation; do not use TEST for tuning.

**Academic integrity limitation:** original gold question ideas were AI-assisted and individually self-reviewed Oct 10. The professor's Friday-before-system independent student-authorship requirement is not established; obtain instructor approval instead of backdating or removing provenance. Keep all private questions and secrets outside public GitHub.

**Documented GitHub review milestone:** PR #14 was formally APPROVED by a different teammate, unlike some earlier merged PRs that lack a formal recorded review. Preserve that evidence. Require formal approvals consistently going forward.
