# Standard Prompt Library

This directory contains curated, ready-to-use prompts for each MCP bundle in the
consulting kit.  Each file is self-contained and maps directly to one bundle.

| File | Bundle | Port |
|------|--------|------|
| [`business-intelligence-mcp.prompts.md`](business-intelligence-mcp.prompts.md) | Business Intelligence MCP | 8101 |
| [`api-integration-hub.prompts.md`](api-integration-hub.prompts.md) | API Integration Hub MCP | 8102 |
| [`content-automation-mcp.prompts.md`](content-automation-mcp.prompts.md) | Content Automation MCP | 8103 |

---

## How Prompts Are Organised

Each prompt file follows the same structure:

```
## <Use-Case Group>

### <Prompt Name>
**Use case:** …
**Expected output format:** …
**Prompt:**
> …
**Quality notes:** …
**Known limitations:** …
**When to customise:** …
```

---

## Usage Guide

### Using prompts with the `/query`, `/slack/message`, `/github/issue`, etc. endpoints

All protected endpoints require an `X-API-Key` header.  The prompt text goes into
the relevant request body field (e.g. `query` for the BI `/query` endpoint, `text`
for the Slack `/slack/message` endpoint).

### Using prompts via the MCP transport (`/mcp`)

Connect any MCP-compatible client (e.g. Claude Desktop) to the server's `/mcp`
endpoint and paste the prompt into the chat window.  The MCP server routes the
request to the correct tool automatically.

### Customising prompts

Prompts marked **When to customise** tell you which parts to adapt for a specific
client engagement.  The most common customisation points are:

- **Table / column names** — replace placeholder names with the client's real schema.
- **Channel names** — replace `#engineering` or `#ops` with the client's Slack channel.
- **Repository** — replace `owner/repo` with the client's actual GitHub repository.
- **Domain constraints** — tighten date ranges, status filters, or record limits to
  match the client's data volume expectations.

### Prompt quality tiers

Each prompt carries a **Quality** badge:

| Badge | Meaning |
|-------|---------|
| ✅ Production-ready | Tested against the reference data set; safe to use in a client demo as-is. |
| 🔧 Requires customisation | Works as a template but needs schema or context adaptation before demo use. |
| 🧪 Experimental | Useful for exploration; output format may be inconsistent across runs. |

---

## Adding New Prompts

1. Open the relevant `<bundle>.prompts.md` file.
2. Add a new `###` subsection under the appropriate use-case group.
3. Fill in all fields (`Use case`, `Expected output format`, `Prompt`, `Quality notes`,
   `Known limitations`, `When to customise`).
4. Submit a pull request; the PR description should include a brief note on what
   scenario the new prompt covers.
