# Prompt Library — API Integration Hub MCP

**Bundle:** `api-integration-hub` | **Port:** 8102

This bundle exposes three integration surfaces, each with its own endpoint and
request shape.  Prompts are grouped by integration and use-case.

| Integration | Endpoint | Request fields |
|-------------|----------|----------------|
| Slack | `POST /slack/message` | `channel`, `text` |
| GitHub | `POST /github/issue` | `owner`, `repo`, `title`, `body`, `notify_slack_channel` |
| Stripe | `POST /stripe/customer` | `customer_id` |

All endpoints require the `X-API-Key` header.

> **When to use the MCP transport instead:** When driving this bundle from a
> Claude Desktop or MCP-compatible client, connect to `POST /mcp` and paste the
> prompt into the chat window.  The MCP router selects the correct tool
> automatically based on the prompt content.

---

## 1. Slack Notifications

Use these prompts to send formatted messages to Slack channels.  The `text` field
supports Slack mrkdwn syntax (bold with `*text*`, italic with `_text_`, code with
`` `text` ``).

### 1.1 Deployment status announcement

**Quality:** ✅ Production-ready

**Use case:** DevOps or engineering team notification after a successful deployment.

**Expected output format:**
```json
{
  "ok": true,
  "channel": "C012AB3CD",
  "ts": "1711900123.000100"
}
```

**Request body:**
```json
{
  "channel": "#engineering",
  "text": "*Deployment complete* ✅\n>Service: `payment-api`\n>Version: `v2.4.1`\n>Environment: *production*\n>Deployed by: @release-bot"
}
```

**Quality notes:**
- Slack's mrkdwn blockquote (`>`) renders cleanly in both desktop and mobile.
- Emoji shortcodes (`:white_check_mark:`) work in `text`; Unicode emoji (✅) also work.

**Known limitations:**
- The `text` field does not support Block Kit attachments through this endpoint;
  for rich card layouts, a direct Slack API call is required.
- Messages are posted as the bot user; the bot must be a member of the target channel.

**When to customise:**
- Replace `#engineering` with the client's channel name or channel ID.
- Update the service name, version, and environment to match the demo scenario.

---

### 1.2 Incident alert

**Quality:** ✅ Production-ready

**Use case:** On-call or SRE team alert during an outage simulation.

**Request body:**
```json
{
  "channel": "#incidents",
  "text": "*🚨 INCIDENT ALERT*\n>Severity: *P1*\n>Affected service: `checkout-api`\n>Symptoms: Elevated 5xx errors (error rate 12%)\n>Detected at: 2024-03-15 14:32 UTC\n>On-call: <@U01234ABCDE>\n\nPlease acknowledge in this thread."
}
```

**Expected output format:** Same shape as 1.1.

**Quality notes:**
- User mentions (`<@USERID>`) trigger Slack notifications; use a channel mention
  (`<!channel>` or `<!here>`) for broader reach.
- For a demo, replace the user ID with a real Slack user ID from the client's workspace.

**Known limitations:**
- The bot must have `chat:write` scope; `<!channel>` additionally requires
  `chat:write.customize` or `chat:write.public`.

**When to customise:**
- Replace severity level, service name, and symptoms.
- Replace `<@U01234ABCDE>` with the client's on-call user ID.

---

### 1.3 Weekly summary report

**Quality:** 🔧 Requires customisation

**Use case:** Automated weekly digest for a management or executive channel.

**Request body:**
```json
{
  "channel": "#weekly-digest",
  "text": "*Weekly Engineering Summary — W12 2024*\n\n*Deployments:* 14 releases across 6 services\n*Incidents:* 1 P2 (resolved in 47 min)\n*Open PRs:* 23 (↓5 vs last week)\n*Test coverage:* 84% (↑2%)\n\n_Full report:_ <https://internal-dashboard.example.com/w12|View dashboard>"
}
```

**Expected output format:** Same shape as 1.1.

**Quality notes:**
- The Slack hyperlink syntax `<URL|label>` renders as a clickable link.
- Numbers should be pre-computed by the caller before sending; the hub does not
  aggregate data — it only delivers messages.

**Known limitations:**
- Long messages may be truncated by Slack at approximately 3000 characters.

**When to customise:**
- Replace all metric values with the client's actual figures.
- Replace the dashboard URL with the client's reporting tool.
- Adjust the week number and date to match the demo context.

---

## 2. GitHub Issue Creation

Use these prompts to create structured issues in GitHub repositories.  The optional
`notify_slack_channel` field triggers an automatic Slack notification after the
issue is created.

### 2.1 Bug report

**Quality:** ✅ Production-ready

**Use case:** Demonstrate automated issue creation from an error monitoring system.

**Expected output format:**
```json
{
  "id": 2147483647,
  "number": 42,
  "title": "NullPointerException in PaymentProcessor.charge() — production",
  "html_url": "https://github.com/acme/payment-api/issues/42",
  "state": "open"
}
```

**Request body:**
```json
{
  "owner": "acme",
  "repo": "payment-api",
  "title": "NullPointerException in PaymentProcessor.charge() — production",
  "body": "## Bug Report\n\n**Environment:** Production\n**Severity:** P1\n**First observed:** 2024-03-15 14:32 UTC\n\n### Steps to reproduce\n1. Call `POST /charge` with a customer whose default payment method has expired.\n2. Observe 500 response with `NullPointerException`.\n\n### Expected behaviour\nReturn a 422 with a descriptive error message.\n\n### Actual behaviour\nServer throws `NullPointerException` at `PaymentProcessor.java:142`.\n\n### Stack trace\n```\njava.lang.NullPointerException\n    at com.acme.payment.PaymentProcessor.charge(PaymentProcessor.java:142)\n```\n\n### Impact\nAffects all checkout flows for customers with expired payment methods.",
  "notify_slack_channel": "#engineering"
}
```

**Quality notes:**
- The Markdown body renders correctly in GitHub's issue view.
- Including `notify_slack_channel` posts the new issue URL to Slack automatically,
  demonstrating the hub's cross-integration orchestration capability.

**Known limitations:**
- Requires `GITHUB_TOKEN` with `issues:write` scope on the target repository.
- If `SLACK_BOT_TOKEN` is not configured, `notify_slack_channel` is silently ignored.

**When to customise:**
- Replace `owner` and `repo` with the client's GitHub organisation and repository.
- Update the title, stack trace, and impact section to match the demo scenario.

---

### 2.2 Feature request

**Quality:** ✅ Production-ready

**Use case:** Product management workflow demo — AI assistant creates a well-structured
feature request from a brief description.

**Request body:**
```json
{
  "owner": "acme",
  "repo": "product-roadmap",
  "title": "feat: add CSV export to the analytics dashboard",
  "body": "## Feature Request\n\n### Summary\nAllow users to export any analytics chart as a CSV file directly from the dashboard.\n\n### Motivation\nSeveral enterprise customers have requested offline data access for compliance reporting.\n\n### Proposed solution\nAdd an *Export CSV* button to each chart component.  The export should include:\n- All visible data points\n- Column headers matching the chart axes\n- A timestamp in the filename (`analytics-export-YYYYMMDD.csv`)\n\n### Acceptance criteria\n- [ ] Export button visible on all chart types\n- [ ] CSV includes headers\n- [ ] Filename includes date\n- [ ] Works in Chrome, Firefox, and Safari\n\n### Out of scope\n- Excel (`.xlsx`) format — follow-up issue\n- Scheduled / automated exports"
}
```

**Expected output format:** Same shape as 2.1.

**Quality notes:**
- GitHub checkbox syntax (`- [ ]`) renders as interactive checkboxes in the issue UI.
- Using `feat:` prefix in the title keeps the issue aligned with conventional commits
  if the client uses that workflow.

**Known limitations:**
- Labels and assignees cannot be set through this endpoint; use the GitHub API
  directly for full issue metadata.

**When to customise:**
- Replace `owner`, `repo`, and the feature description with client-specific content.

---

### 2.3 Incident post-mortem tracking issue

**Quality:** 🔧 Requires customisation

**Use case:** Incident management demo — auto-generate a post-mortem tracking issue
after an alert fires.

**Request body:**
```json
{
  "owner": "acme",
  "repo": "incident-tracker",
  "title": "Post-mortem: checkout-api P1 outage — 2024-03-15",
  "body": "## Incident Post-Mortem\n\n| Field | Value |\n|-------|-------|\n| Incident ID | INC-2024-0315 |\n| Severity | P1 |\n| Duration | 47 minutes |\n| Affected service | `checkout-api` |\n| Detection method | PagerDuty alert |\n| Root cause | TBD |\n\n### Timeline\n| Time (UTC) | Event |\n|------------|-------|\n| 14:32 | Alert fired |\n| 14:38 | On-call engineer paged |\n| 15:02 | Root cause identified |\n| 15:19 | Fix deployed to production |\n\n### Action items\n- [ ] Add null-check in `PaymentProcessor.charge()`\n- [ ] Improve error handling for expired payment methods\n- [ ] Add monitoring alert for this error class\n\n### Next review date\n2024-03-22",
  "notify_slack_channel": "#incidents"
}
```

**Expected output format:** Same shape as 2.1.

**Quality notes:**
- GitHub Markdown tables render cleanly; keep the `|---|---|` separator row.

**Known limitations:**
- Auto-fill of timeline entries requires the caller to inject real timestamps
  before sending the request; the hub does not pull data from external sources.

**When to customise:**
- Update the incident ID, duration, root cause, and timeline.
- Replace the action items with the real corrective actions identified.

---

## 3. Stripe Customer Lookup

Use these prompts to retrieve customer, charge, and subscription data from Stripe.

> **Important:** Always use test-mode customer IDs (`cus_test_…`) during demos.
> Never use live production customer IDs in a demo environment.

### 3.1 Basic customer profile lookup

**Quality:** ✅ Production-ready

**Use case:** Show a sales or support team how to pull a unified customer view from
Stripe in one API call.

**Expected output format:**
```json
{
  "customer": {
    "id": "cus_TestABCD1234",
    "email": "alice@example.com",
    "name": "Alice Example",
    "created": 1700000000,
    "metadata": {}
  },
  "charges": {
    "data": [
      { "id": "ch_TestXYZ", "amount": 9900, "currency": "usd", "status": "succeeded", "created": 1711900000 }
    ]
  },
  "subscriptions": {
    "data": [
      { "id": "sub_TestLMN", "status": "active", "current_period_end": 1714492000 }
    ]
  }
}
```

**Request body:**
```json
{
  "customer_id": "cus_TestABCD1234"
}
```

**Quality notes:**
- The response aggregates three Stripe API calls into one payload, demonstrating
  the hub's value as an orchestration layer.
- `amount` is returned in the currency's smallest unit (cents for USD); divide by
  100 for display.

**Known limitations:**
- `customer_id` must be a Stripe customer ID (`cus_…`); lookup by email is not
  supported through this endpoint.
- Requires `STRIPE_API_KEY` to be configured; the endpoint returns HTTP 500 if
  the key is absent.
- The charge and subscription lists are paginated by Stripe; only the first page
  (default 10 items) is returned.

**When to customise:**
- Replace `cus_TestABCD1234` with a real test-mode customer ID from the client's
  Stripe test environment.

---

### 3.2 Subscription status check

**Quality:** ✅ Production-ready

**Use case:** Customer-success or billing team demo — verify a customer's active
subscription before a support interaction.

**Request body:**
```json
{
  "customer_id": "cus_TestABCD1234"
}
```

**Prompt guidance (MCP transport):**
> Look up the Stripe customer with ID `cus_TestABCD1234` and tell me whether they
> have an active subscription and when it renews.

**Quality notes:**
- When using the MCP transport, the model interprets the response and provides a
  human-readable summary, making this prompt ideal for non-technical stakeholders.
- `current_period_end` is a Unix timestamp; instruct the model to convert it to a
  human-readable date in the prompt.

**Known limitations:**
- Cancelled subscriptions appear in the list with `status: "canceled"`; the model
  should be prompted to filter for `status: "active"` explicitly if needed.

**When to customise:**
- Replace the customer ID.
- When using direct API (not MCP transport), post-process `current_period_end` in
  the calling application.

---

### 3.3 Payment history overview

**Quality:** 🔧 Requires customisation

**Use case:** Finance or AR team demo — retrieve recent payment history for a customer.

**Request body:**
```json
{
  "customer_id": "cus_TestABCD1234"
}
```

**Prompt guidance (MCP transport):**
> Pull up the Stripe record for customer `cus_TestABCD1234`.  List their last
> 10 charges with date, amount in USD, and success/failure status.

**Quality notes:**
- The charges list is returned under `charges.data`; the MCP model can format it
  as a table if instructed.

**Known limitations:**
- Only the first page of charges (≤ 10 items) is returned per request.
- Refunds are not included in the charge list; they appear as separate objects in
  the Stripe API and are not surfaced by this endpoint.

**When to customise:**
- Replace the customer ID with a test-mode ID from the client's Stripe account.
- If the client needs more than 10 charges, this endpoint requires a code-level
  change to increase the Stripe API `limit` parameter.
