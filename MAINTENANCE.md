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

