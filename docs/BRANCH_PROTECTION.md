# MSAI 633 collaboration controls — ACTION REQUIRED BY REPO ADMIN

These settings **cannot** be inferred from code, GitHub Actions or a PR. A repository administrator must verify them in the GitHub UI and capture dated screenshots for the course.

1. Open https://github.com/2023lokesh/carebridge-rag/settings/rules and create a ruleset targeting `main`.
2. Require pull requests before merging, at least **one approval by another student**, dismiss stale reviews after pushes, block force pushes and deletions, and require the `Tests / test` status check. Configure applicable admin bypass restrictions. GitHub plan/org restrictions may affect availability.
3. Confirm each of the five **distinct** teammates has GitHub access and independently contributes to >1 pipeline stage. Record PR links, reviewer approval, owner and commit SHA in `reports/06_final_performance.md`.
4. Assign the existing Issues #1–#5 to real GitHub usernames, apply labels/states, and keep the board updated. Do not guess usernames or fabricate reviews.
5. For all future changes: branch -> open PR -> teammate reviews/approves -> merge to `main`. Existing historical direct pushes cannot be retroactively made compliant; **disclose them**.
6. In Settings -> Secrets and variables -> Actions, set secret `CRAWL_CONTACT_EMAIL` to a real, approved contact address before manually running **Actions -> Collect and audit public CDC corpus**. No patient data or credentials are required for crawling public CDC content.

**Review evidence template:** Date: ___ | Ruleset link: ___ | Screenshot: ___ | Approving teammate: ___ | Approved PR: ___ | Other member commits: ___.
