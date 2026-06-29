# Maintenance Log

_Newest entries at top. Full git log for older entries._

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

## 2026-06-26

- Node.js updates: PR #68 (app), PR #69 (frontend) opened
- Python: pip checks ran in system context — no actionable data

## 2026-06-25

- Full dependency audit: 19/24 Python packages outdated, 5 critical major bumps (openai, redis, praw, mastodon.py, anthropic)
- No auto-upgrade performed — manual review needed

## 2026-06-24

- Initial maintenance run
- Node.js (app, frontend): all at latest per semver ranges
- Python: audit completed, major version bumps identified
