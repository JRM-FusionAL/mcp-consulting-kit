# Bundle Validation Checklist

Use this checklist to verify that each bundle manifest is complete and that the
corresponding service is ready for a repeatable client deployment.

Run through **all three sections** before handing a bundle to a client or
promoting it to production.

---

## How to Use

1. Open the relevant manifest (`bundles/<bundle-name>.manifest.yaml`).
2. Work through each item below.  Check the box when the criterion is met.
3. If any item cannot be checked, resolve the gap before proceeding.
4. Sign off at the bottom once all items pass.

---

## Section 1 — Manifest Structure

These items apply to every manifest and must be verified once per file.

- [ ] `manifest_version` field is present and set to `"1"`.
- [ ] `bundle_version` follows semver (`MAJOR.MINOR.PATCH`).
- [ ] `name` matches the directory name under `showcase-servers/`.
- [ ] `display_name` is a human-readable label.
- [ ] `description` accurately describes what the service does.
- [ ] `port` matches the value in the service's `Dockerfile` and `docker-compose.yaml`.
- [ ] `dockerfile` path resolves to an existing file in the repository.
- [ ] `startup_order.position` is set and reflects correct launch sequencing.
- [ ] `startup_order.depends_on` lists every upstream service the bundle needs.
- [ ] Each dependency in `depends_on` has a `health_check` command.
- [ ] `dependencies.python_version` matches the `FROM` line in the `Dockerfile`.
- [ ] Every package in `dependencies.packages` matches the pinned version in
      the service's `requirements.txt`.  No package is missing; no extra package
      is listed.
- [ ] `health_check.endpoint`, `method`, and `expected_status` are filled in.
- [ ] `endpoints` lists every publicly exposed route.

---

## Section 2 — Environment / Configuration Contract

For each entry in the manifest's `env` block, verify:

- [ ] Every env var that appears in the service's `.env.example` file is
      represented in the manifest.
- [ ] Every env var in the manifest that is marked `required: true` is
      documented in `.env.example`.
- [ ] Every env var marked `secret: true` is **absent** from
      version-controlled `.env` files (only `.env.example` may be committed).
- [ ] Each env var has a non-empty `description` that explains its purpose.
- [ ] Each env var has an `example` value that is safe to share publicly
      (i.e., the example does not contain a real secret).
- [ ] Optional vars (`required: false`) have a `default` value recorded
      wherever the application applies one.
- [ ] The `API_KEY` / `API_KEYS` / `REVOKED_API_KEYS` rotation model is
      documented for every bundle.
- [ ] `REDIS_URL` degraded-fallback behaviour (in-process store) is noted.

---

## Section 3 — Per-Bundle Spot Checks

### 3a — Business Intelligence MCP (`business-intelligence-mcp.manifest.yaml`)

- [ ] `DB_URL` is listed as `required: true` with a description of all
      supported database connection-string formats.
- [ ] `LLM_PROVIDER` documents all accepted values (`claude`, `rule`, `local`)
      and notes that `local` is a placeholder.
- [ ] `ANTHROPIC_API_KEY` is listed as `required: false` and its condition
      (only needed when `LLM_PROVIDER=claude`) is explained.
- [ ] Port is `8101` in both the manifest and `docker-compose.yaml`.
- [ ] The `/query` endpoint is listed with `auth_required: true`.
- [ ] The `/mcp` MCP transport endpoint is listed.

### 3b — API Integration Hub (`api-integration-hub.manifest.yaml`)

- [ ] `SLACK_BOT_TOKEN`, `GITHUB_TOKEN`, and `STRIPE_API_KEY` are all listed
      as `required: false` (add only what the client needs).
- [ ] Each third-party secret has a note indicating when it is required.
- [ ] Port is `8102` in both the manifest and `docker-compose.yaml`.
- [ ] The `/slack/message`, `/github/issue`, and `/stripe/customer` endpoints
      are listed with `auth_required: true`.
- [ ] The `/mcp` MCP transport endpoint is listed.

### 3c — Content Automation MCP (`content-automation-mcp.manifest.yaml`)

- [ ] `beautifulsoup4`, `lxml`, and `feedparser` are all listed under
      `dependencies.packages` with pinned versions matching `requirements.txt`.
- [ ] Port is `8103` in both the manifest and `docker-compose.yaml`.
- [ ] The `/scrape/article`, `/scrape/links`, `/scrape/tables`, and
      `/rss/parse` endpoints are listed with `auth_required: true`.
- [ ] The `/mcp` MCP transport endpoint is listed.

---

## Section 4 — Prompt Library

- [ ] The manifest includes a `prompt_library` field pointing to the correct file
      under `bundles/prompts/`.
- [ ] The prompt file exists at the path stated in `prompt_library`.
- [ ] The prompt file contains at least one prompt per major use-case group for
      the bundle.
- [ ] Every prompt entry includes: `Use case`, `Expected output format`, `Prompt`
      (or `Request body`), `Quality notes`, `Known limitations`, and
      `When to customise`.
- [ ] Each prompt carries a quality badge: ✅ Production-ready, 🔧 Requires
      customisation, or 🧪 Experimental.

---

## Section 5 — Deployment Readiness

- [ ] A `.env` file (copied from `.env.example`) exists for the service and
      contains real values for every `required: true` env var.
- [ ] The `.env` file is **not** committed to version control.
- [ ] The Docker image builds successfully (`docker build -t <name> .`).
- [ ] The container starts and `/health` returns HTTP 200.
- [ ] At least one protected endpoint returns HTTP 401 when called without a
      valid `X-API-Key` header.
- [ ] At least one protected endpoint returns the expected response when called
      with a valid `X-API-Key` header.
- [ ] The service is reachable on its documented port from the host machine.

---

## Sign-Off

| Bundle | Checked by | Date | Notes |
|--------|-----------|------|-------|
| business-intelligence-mcp | | | |
| api-integration-hub | | | |
| content-automation-mcp | | | |
