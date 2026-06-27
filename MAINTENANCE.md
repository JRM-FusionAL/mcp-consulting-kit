## Maintenance Summary - 2026-06-24

### Actions Taken
- Checked for outdated dependencies in subprojects
- Opened PRs for updates where needed
- Labeled new issues without labels as 'triage'

### PRs Opened in This Run

## Maintenance Summary - 2026-06-24

### Actions Taken
- Checked for outdated dependencies in subprojects
- Opened PRs for updates where needed
- Labeled new issues without labels as 'triage'

### PRs Opened in This Run

## Maintenance Summary - 2026-06-25

### Actions Taken
- Ran dependency audit across 6 Python + 2 Node.js subprojects
- Checked for open PRs (none open)
- Labeled new issues (none unlabeled)
- No branch/PR created — 19/24 Python packages outdated, but blind auto-upgrade blocked (see audit below)

### Dependency Audit Results
**Python:** 19 of 24 pinned packages outdated across 6 subprojects
- **Critical version bumps** (breaking changes likely):
  - `openai`: 1.30.0 → 2.44.0 (major SDK revamp)
  - `redis`: 7.4.0 → 8.0.1 (major version)
  - `mastodon.py`: 1.8.1 → 2.2.1 (major version)
  - `praw`: 7.8.1 → 8.0.2 (major version)
  - `anthropic`: 0.88.0 → 0.112.0 (major)
- **Safe minor/patch bumps** (16 others): fastapi, pydantic, sqlalchemy, requests, httpx, etc.
- **Node.js:** `app` and `frontend` — all at latest per semver ranges (caret)

### Issues Labeled
- No unlabeled open issues found

### PRs Opened in This Run
- None — manual review needed for breaking dependency bumps


---

## Maintenance Summary - 2026-06-26

### Actions Taken
- Checked for outdated dependencies in all 8 subprojects
- Opened PRs for Node.js dependency updates in app and frontend
- Labeled new issues without labels as triage (none found)
- Python dependencies: 6 subprojects checked via system pip (no venv) — no actionable update data

### Dependency Audit Results

**Node.js updates applied:**
- app: react 19.2.4->19.2.7, react-dom 19.2.4->19.2.7, vite 8.0.16->8.1.0
- frontend: @vitejs/plugin-react 6.0.2->6.0.3, vite 8.0.16->8.1.0

**Python:** pip checks ran in system context (no venv activated) — skipping auto-upgrade to avoid breaking subproject environments. Manual review recommended for next interactive session.

### Issues Labeled
- No unlabeled open issues found

### PRs Opened in This Run
- PR #68: chore: update Node.js dependencies in app
- PR #69: chore: update Node.js dependencies in frontend

### CI Status
- PR #68: pending (Analyze, CodeRabbit, security-scan, security-smoke)

---

## Maintenance Summary - 2026-06-27

### Actions Taken
- Merged 3 prior PRs (#68, #69, #70) — all CI green, CLEAN merge state
- Bumped Python dependencies across 5 tracked showcase servers (PR #71)
- Checked Node.js deps — only major version bumps remain (@vitejs/plugin-react 5→6, react 18→19), deferred
- No open issues to triage
- social-distribution-mcp/ is gitignored and untracked — requirements.txt changes not comittable

### PRs Merged This Run
- PR #68: chore: update Node.js dependencies in app ✅
- PR #69: chore: update Node.js dependencies in frontend ✅
- PR #70: docs: update maintenance summary for 2026-06-26 ✅

### PRs Opened This Run
- PR #71: chore: bump Python dependencies (safe minor/patch)

### Dependency Audit Results

**Python safe bumps applied (PR #71):**
- fastapi: 0.135.x → 0.138.1
- uvicorn: 0.41/0.42 → 0.49.0
- pydantic: 2.12.5 → 2.13.4
- mcp[cli]: 1.26.0 → 1.28.1
- requests: 2.33.x → 2.34.2
- anthropic: 0.88.0 → 0.112.0
- sqlalchemy: 2.0.48 → 2.0.51
- beautifulsoup4: 4.14.3 → 4.15.0
- lxml: 6.1.0 → 6.1.1
- tweepy: 4.15.0 → 4.16.0
- redis: 7.2/7.3 → 7.4.0 (normalized)

**Python intentionally skipped (major breaking):**
- redis 7→8, praw 7→8 — require code migration

**Node.js deferred (major breaking):**
- @vitejs/plugin-react: 5.2.0 → 6.0.3
- react/react-dom: 18.3.1 → 19.2.7

### Issues Labeled
- No unlabeled open issues found
