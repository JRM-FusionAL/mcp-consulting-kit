# Maintenance Log

_Newest entries at top. Full git log for older entries._

---

## 2026-07-01

### Actions Taken
- Checked for outdated dependencies in subprojects
- Opened PRs for Python dependency updates where needed
- Labeled new issues without labels as 'triage'
- Merged PR #75 (maintenance summary for 2026-06-30)
- Fixed maintenance script to filter pip freeze output (avoid pulling in system packages like aptdaemon)
- Closed duplicate PR #76 (superseded by #77)

### PR Status (opened this run)
| PR | Subproject | Status | Notes |
|----|------------|--------|-------|
| #77 | api-integration-hub | MERGEABLE | CodeQL ✅, Security smoke ✅, **Security scan FAIL** (pip-audit: aptdaemon not on PyPI) |
| #78 | business-intelligence-mcp | MERGEABLE | CodeQL ✅, **Security smoke FAIL**, **Security scan FAIL** (pip-audit: aptdaemon) |
| #79 | content-automation-mcp | MERGEABLE | CodeQL ✅, Security smoke ✅, **Security scan FAIL** (pip-audit: aptdaemon) |

### Key Issues
- **pip-audit failure**: The security scan runs `pip-audit` against all Python subprojects. It fails because `pip freeze` in the maintenance script picked up system packages (`aptdaemon==2.0.2`, `apturl==0.5.2`, etc.) that don't exist on PyPI. Fixed by filtering `pip freeze` output to only packages listed in the original `requirements.txt`.

### Next Steps
- Re-run maintenance with fixed script (non-dry-run) to regenerate clean requirements.txt files
- Re-push fixed branches to trigger passing CI
- Merge PRs once security-scan passes

---

## 2026-06-30

- **Pulled latest main** (fast-forward to fc1a025, PR #74 merged)
- **PR #74**: Potential fix for code scanning alert #11 (clear-text logging of sensitive info) ✅ merged 2026-06-28
- **PR #73**: docs: update maintenance summary for 2026-06-28 ✅ merged 2026-06-28
- **Dependency audit**: pip unreliable in cron context (aliases to FusionAL venv). Node.js confirmed: `app` @vitejs/plugin-react 5.2.0→6.0.3, `frontend` react/react-dom 18.3.1→19.2.7 (both major-breaking, deferred)
- **No open issues** to triage
- **No open PRs** to merge
- **No branches/PRs opened** this run

---

## 2026-06-29

- **Pulled latest main** (fast-forward to fc1a025, PR #74 merged)
- **PR #74**: Potential fix for code scanning alert #11 (clear-text logging of sensitive info) ✅ merged 2026-06-28
- **PR #73**: docs: update maintenance summary for 2026-06-28 ✅ merged 2026-06-28
- **Dependency audit**: pip unreliable in cron context (aliases to FusionAL venv). Node.js confirmed: `app` @vitejs/plugin-react 5.2.0→6.0.3, `frontend` react/react-dom 18.3.1→19.2.7 (both major-breaking, deferred)
- **No open issues** to triage
- **No open PRs** to merge
- **No branches/PRs opened** this run

---

## 2026-06-27

- Merged PRs #68 (Node.js app deps), #69 (Node.js frontend deps), #70 (summary docs)
- Opened PR #71: Python safe minor/patch bumps (12 packages)
- Node.js major bumps deferred (react 18→19, @vitejs/plugin-react 5→6)

---

## 2026-06-26

- Node.js updates: PR #68 (app), PR #69 (frontend) opened
- Python: pip checks ran in system context — no actionable data

---

## 2026-06-25

- Full dependency audit: 19/24 Python packages outdated, 5 critical major bumps (openai, redis, praw, mastodon.py, anthropic)
- No auto-upgrade performed — manual review needed

---

## 2026-06-24

- Initial maintenance run
- Node.js (app, frontend): all at latest per semver ranges
- Python: audit completed, major version bumps identified## Maintenance Summary - 2026-07-01

### Actions Taken
- Checked for outdated dependencies in subprojects
- Opened PRs for updates where needed
- Labeled new issues without labels as 'triage'

### PRs Opened in This Run
- PR #80

