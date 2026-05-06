# CLAUDE.md — mcp-consulting-kit

The repo of MCP showcase servers and consulting deliverables. Future home of `recall/` and `kb-bridge/` install templates (not yet — see PRIORITIES P2 #13).

---

## SESSION INIT — RUN THIS FIRST

Before responding to anything, in this order:

1. Read `C:\Users\puddi\Projects\fusional-knowledge-base\00-CURRENT-STATUS\STATUS.md`
2. Read `C:\Users\puddi\Projects\fusional-knowledge-base\00-CURRENT-STATUS\PRIORITIES.md`
3. Read `C:\Users\puddi\Projects\fusional-knowledge-base\05-RECALL\SOLVED-ISSUES.md`
4. State runtime: "Running as: <model> on <platform>, tools available: <summary>"

---

## RECALL PROTOCOL (mandatory, visible)

Before debugging ANY error or unexpected behavior:
1. State "Recall check: searching SOLVED-ISSUES for <error fingerprint>"
2. Check the registry (loaded in session init)
3. State outcome: "Match: SI-XXX — applying documented fix" OR "No match — proceeding with new diagnosis"

The Recall check is VISIBLE OUTPUT. If the line is not in the response, the check did not happen.

---

## AUTO-LOG PROTOCOL (mandatory, ambient)

While working on any task, monitor for these AUTO-LOG TRIGGERS:

1. **Wrong assumption corrected** — agent stated/assumed X, evidence showed Y, time was wasted
2. **Path/config drift discovered** — documented value doesn't match reality on disk/runtime
3. **Command failed and root cause identified** — error + fix found, would re-bite future sessions
4. **Protocol violation caught** — Recall check skipped, runtime not declared, etc.
5. **Cross-system surprise** — case sensitivity, line endings, branch divergence, version mismatch
6. **"Why isn't this working" → resolution** — anything that took >2 minutes to diagnose
7. **Repeated pattern** — same kind of mistake hitting twice = systemic, log it

When a trigger fires:
1. State: "Auto-log trigger: <which trigger> — drafting SI-XXX"
2. Read `C:\Users\puddi\Projects\fusional-knowledge-base\05-RECALL\SOLVED-ISSUES.md` to find highest existing SI number
3. Append the new entry IMMEDIATELY (do not defer to end of session)
4. Insert before "## TEMPLATE — copy this for new entries" using filesystem tools
5. Confirm: "Logged SI-XXX: <title>"
6. Continue the original task

Do NOT ask permission to log. Do NOT batch logs. Do NOT skip when "not sure if it's worth logging" — log it.

Format (strict):
```
## SI-XXX: <one-line title>
**Symptoms:** <what you saw>
**Root cause:** <what was actually wrong>
**Fix:** <exact steps that worked>
**Verified:** YYYY-MM | **Source:** <session/task context>
**Tags:** <comma-separated>
```

---

## REPO CONTEXT — mcp-consulting-kit

This is the showcase + consulting deliverable repo. Contains:

- `showcase-servers/` — production-grade MCP servers (BI, API hub, content automation, intelligence, github-mcp-safe, social-poster)
- `bundles/` — pre-configured client deployment bundles
- `consulting-materials/` — sales docs, case studies, deliverable templates
- `docker-compose.yaml` — local stack for all showcase servers
- `docker-compose.fusional.yaml` — integration with FusionAL gateway
- `frontend/` — UI for client demos

### Cross-repo dependencies
- `FusionAL` (gateway) imports from `showcase-servers/common/` (security, audit, tracing modules). Do not break that interface.
- `christopher-ai` connects to showcase servers via `FUSIONAL_*_URL` env vars.

### Future additions (NOT YET — gated by PRIORITIES)
- `recall/` — install template for FusionAL Recall MCP (deferred until Recall MCP ships)
- `kb-bridge/` — install template for KB Bridge service (deferred until KB Bridge ships)

**Do not create these directories prematurely.** They are products that get *referenced* from this kit, not built inside it. See SI-009 — cross-product conflation.

---

## CRITICAL FAILURE MODES (already logged — do not repeat)

- **SI-001**: Claude Desktop server timeout above 8 servers — consolidate via FusionAL gateway
- **SI-007**: Don't assume runtime/access mode — verify with environment check
- **SI-008**: Recall check must be VISIBLE OUTPUT, not internal step
- **SI-009**: Don't conflate distinct products in handoff prompts (origin of this rule)
- **SI-011**: Don't `git --amend` after pushing — causes T3610 divergence

Read full registry for details: `C:\Users\puddi\Projects\fusional-knowledge-base\05-RECALL\SOLVED-ISSUES.md`

---

## WORKING RULE

If repo/runtime facts conflict with docs, trust verified code/runtime facts. Call out the mismatch and update the knowledge base during the same task — that's a SI-XXX entry.
