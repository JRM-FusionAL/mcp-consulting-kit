# Prompt Library — Content Automation MCP

**Bundle:** `content-automation-mcp` | **Port:** 8103

This bundle exposes four extraction tools, each with its own endpoint.

| Tool | Endpoint | Request fields |
|------|----------|----------------|
| Article extraction | `POST /scrape/article` | `url` |
| Link harvesting | `POST /scrape/links` | `url` |
| Table parsing | `POST /scrape/tables` | `url` |
| RSS / Atom feed | `POST /rss/parse` | `url`, `limit` |

All endpoints require the `X-API-Key` header.

> **When to use the MCP transport instead:** Connect a Claude Desktop or
> MCP-compatible client to `POST /mcp` and describe the extraction task in plain
> English.  The MCP router selects the correct scraping tool automatically.

---

## 1. Article Extraction

Use these prompts with `POST /scrape/article`.  The endpoint returns the article's
title, main text body, and any metadata the scraper can detect (author, publish date).

### 1.1 News article summary

**Quality:** ✅ Production-ready

**Use case:** Demonstrate automated content ingestion from a news site or blog for a
media, marketing, or research demo.

**Expected output format:**
```json
{
  "url": "https://example.com/articles/ai-trends-2024",
  "title": "Top AI Trends Shaping 2024",
  "text": "Artificial intelligence continues to reshape industries at an unprecedented pace…",
  "author": "Jane Smith",
  "published_date": "2024-03-10"
}
```

**Request body:**
```json
{
  "url": "https://example.com/articles/ai-trends-2024"
}
```

**Prompt guidance (MCP transport):**
> Extract the full article text from `https://example.com/articles/ai-trends-2024`
> and give me a three-sentence summary.

**Quality notes:**
- BeautifulSoup + lxml reliably extracts article content from standard CMS layouts
  (WordPress, Ghost, standard HTML5 `<article>` tags).
- Paywalled content will return only what is visible before the paywall; do not
  use this tool to circumvent access controls.

**Known limitations:**
- JavaScript-heavy SPAs (React, Angular, Vue) may return empty or partial text
  because the scraper does not execute client-side JavaScript.
- Some sites serve different content based on User-Agent; the scraper uses a
  default Python `httpx` agent.
- `author` and `published_date` fields are best-effort; they will be `null` if
  the page does not include standard metadata tags (`<meta name="author">`,
  Open Graph `article:published_time`, etc.).

**When to customise:**
- Replace the URL with a public article from the client's industry vertical.
- For sites that block default user agents, the scraper layer (`scraper.py`) can
  be extended with a custom `User-Agent` header.

---

### 1.2 Press release ingestion

**Quality:** ✅ Production-ready

**Use case:** PR or communications team demo — pull competitor press releases into
a content pipeline.

**Request body:**
```json
{
  "url": "https://newsroom.example.com/press-releases/q1-2024-results"
}
```

**Prompt guidance (MCP transport):**
> Fetch the press release at `https://newsroom.example.com/press-releases/q1-2024-results`
> and extract the headline, key financial metrics mentioned, and any forward-looking
> statements.

**Quality notes:**
- Press release pages on IR (investor relations) sites typically use clean HTML
  and return high-quality extraction results.

**Known limitations:**
- PDF press releases embedded via `<iframe>` or linked as `.pdf` are not extracted;
  only the HTML content is processed.

**When to customise:**
- Replace the URL with a public press release relevant to the client's industry.

---

### 1.3 Blog post monitoring

**Quality:** 🔧 Requires customisation

**Use case:** Competitive intelligence demo — monitor a competitor's blog for new posts.

**Request body:**
```json
{
  "url": "https://competitor.example.com/blog/latest-post"
}
```

**Prompt guidance (MCP transport):**
> Scrape the article at `https://competitor.example.com/blog/latest-post` and
> identify the main topic, target audience, and any product features mentioned.

**Quality notes:**
- Best used in combination with the RSS feed tool (section 4) to first discover
  new post URLs, then extract each article individually.

**Known limitations:**
- Automated scraping of competitor sites should comply with the site's
  `robots.txt` and terms of service; confirm with the client before demo use.

**When to customise:**
- Replace the URL with a publicly accessible blog post.

---

## 2. Link Harvesting

Use these prompts with `POST /scrape/links`.  The endpoint returns a list of all
`<a href="…">` URLs found on the page.

### 2.1 Site navigation map

**Quality:** ✅ Production-ready

**Use case:** SEO or content audit demo — discover all linked pages from a site's
homepage or sitemap.

**Expected output format:**
```json
{
  "url": "https://example.com",
  "links": [
    "https://example.com/about",
    "https://example.com/products",
    "https://example.com/blog",
    "https://example.com/contact",
    "https://twitter.com/exampleco"
  ]
}
```

**Request body:**
```json
{
  "url": "https://example.com"
}
```

**Prompt guidance (MCP transport):**
> Harvest all links from `https://example.com` and group them into internal links
> (same domain) and external links.

**Quality notes:**
- The response includes both absolute and relative URLs; relative URLs are resolved
  against the base URL by the scraper.
- External social media and CDN links are included; filter by domain in the calling
  application if only internal links are needed.

**Known limitations:**
- Only the links present on the single requested page are returned; this is not a
  recursive site crawler.
- JavaScript-rendered navigation menus may not appear in the extracted link list.
- Very large pages may return hundreds of links; the caller should apply client-side
  filtering or pagination.

**When to customise:**
- Replace the URL with the client's homepage or a specific section page.
- Post-process the `links` array in the application to filter by domain or path prefix.

---

### 2.2 Documentation index harvesting

**Quality:** 🔧 Requires customisation

**Use case:** Developer tools or documentation platform demo — build an index of all
docs pages automatically.

**Request body:**
```json
{
  "url": "https://docs.example.com/api/reference"
}
```

**Prompt guidance (MCP transport):**
> Harvest all links from `https://docs.example.com/api/reference`.  List only the
> links that start with `/api/` and remove any anchor fragments.

**Quality notes:**
- Filtering by path prefix in the MCP prompt produces a cleaner output for demos.
- Useful as a first step before batch-scraping each docs page.

**Known limitations:**
- Auth-gated documentation pages (login required) will return a redirect or login
  page's links rather than the docs index.

**When to customise:**
- Replace the URL with the client's documentation site.
- Specify the path prefix to filter in the MCP transport prompt.

---

### 2.3 Job listing discovery

**Quality:** 🔧 Requires customisation

**Use case:** HR or talent intelligence demo — discover open job postings from a
careers page.

**Request body:**
```json
{
  "url": "https://careers.example.com/jobs"
}
```

**Prompt guidance (MCP transport):**
> Get all links from `https://careers.example.com/jobs` and list only those that
> contain `/jobs/` in the URL path — these are individual job posting pages.

**Quality notes:**
- Careers pages with infinite scroll or JavaScript-powered job boards may return
  few or no job links; see Known limitations.

**Known limitations:**
- SPA-based careers pages (Greenhouse, Lever, Workday embeds) do not expose their
  listings in static HTML; this tool will not reliably discover those listings.

**When to customise:**
- Replace the URL with the client's careers page.
- Adjust the URL path filter pattern to match the client's job listing URL structure.

---

## 3. Table Parsing

Use these prompts with `POST /scrape/tables`.  The endpoint parses all `<table>`
elements on the page and returns them as structured arrays of objects.

### 3.1 Financial data table

**Quality:** ✅ Production-ready

**Use case:** Finance or research demo — pull structured data from a public financial
table (e.g. stock screener, earnings summary, government data portal).

**Expected output format:**
```json
{
  "url": "https://example.com/financials/q1-2024",
  "tables": [
    {
      "headers": ["Metric", "Q1 2024", "Q1 2023", "YoY Change"],
      "rows": [
        { "Metric": "Revenue", "Q1 2024": "$142.5M", "Q1 2023": "$118.2M", "YoY Change": "+20.6%" },
        { "Metric": "Gross Profit", "Q1 2024": "$71.3M", "Q1 2023": "$55.4M", "YoY Change": "+28.7%" }
      ]
    }
  ]
}
```

**Request body:**
```json
{
  "url": "https://example.com/financials/q1-2024"
}
```

**Prompt guidance (MCP transport):**
> Parse the financial tables from `https://example.com/financials/q1-2024` and
> identify the row with the highest year-over-year growth.

**Quality notes:**
- lxml's table parser handles merged cells (`colspan`, `rowspan`) gracefully for
  simple two-level headers; deeply nested headers may produce unexpected column names.
- Tables with no `<thead>` row use the first `<tr>` as headers automatically.

**Known limitations:**
- Tables generated by JavaScript charting libraries (Highcharts, D3) do not appear
  in the HTML DOM and will not be extracted.
- Extremely wide tables (50+ columns) may produce column key collisions if headers
  are not unique.

**When to customise:**
- Replace the URL with a page containing real financial or operational data relevant
  to the client's industry.
- If the page contains multiple tables, post-process the `tables` array to select
  the relevant one by index or header keyword.

---

### 3.2 Government statistics table

**Quality:** ✅ Production-ready

**Use case:** Public sector or research demo — extract structured data from a
government data portal.

**Request body:**
```json
{
  "url": "https://data.example.gov/statistics/employment-2024"
}
```

**Prompt guidance (MCP transport):**
> Extract the employment statistics table from
> `https://data.example.gov/statistics/employment-2024` and format it as a
> markdown table with the headers left-aligned.

**Quality notes:**
- Government sites typically use well-structured HTML tables and return the most
  reliable extraction results.

**Known limitations:**
- Multi-page tables (pagination) require separate requests per page; the scraper
  does not follow "Next page" links automatically.

**When to customise:**
- Replace the URL with the specific data portal page relevant to the client's domain.

---

### 3.3 Pricing comparison table

**Quality:** 🔧 Requires customisation

**Use case:** Competitive analysis demo — pull pricing tiers from a competitor's
pricing page.

**Request body:**
```json
{
  "url": "https://competitor.example.com/pricing"
}
```

**Prompt guidance (MCP transport):**
> Scrape the pricing table from `https://competitor.example.com/pricing` and
> list each plan name with its monthly price and the three most important features.

**Quality notes:**
- Pricing tables built with CSS Grid or Flexbox without a `<table>` element will
  not be extracted by this tool; use the article extraction tool as a fallback.
- HTML `<table>`-based pricing grids (common on older SaaS sites) extract well.

**Known limitations:**
- Pricing pages that use JavaScript to toggle annual/monthly pricing may only
  return one pricing variant depending on the default state of the page.
- Prices displayed as images rather than text cannot be extracted.

**When to customise:**
- Replace the URL with the client's competitor's pricing page.
- If the page uses CSS layout instead of HTML tables, switch to
  `POST /scrape/article` and parse the text manually.

---

## 4. RSS / Atom Feed Parsing

Use these prompts with `POST /rss/parse`.  The endpoint fetches and parses an RSS
or Atom feed and returns structured entries with title, link, summary, and published
date.  All prompts in this section use the same request shape:

```jsonc
// Request shape (applies to all RSS prompts below)
{
  "url": "https://example.com/feed.xml",
  "limit": 20   // optional, default 20; reduce to 5-10 for quick demos
}
```

### 4.1 Industry news feed

**Quality:** ✅ Production-ready

**Use case:** Market intelligence or news aggregation demo — pull the latest articles
from an industry publication's RSS feed.

**Expected output format:**
```json
{
  "feed_title": "TechCrunch",
  "entries": [
    {
      "title": "AI Startup Raises $50M Series B",
      "link": "https://techcrunch.com/2024/03/15/ai-startup-raises-50m",
      "summary": "A San Francisco-based AI startup announced today that it has closed…",
      "published": "Fri, 15 Mar 2024 14:00:00 +0000"
    }
  ]
}
```

**Request body:**
```json
{
  "url": "https://techcrunch.com/feed/",
  "limit": 10
}
```

**Prompt guidance (MCP transport):**
> Parse the TechCrunch RSS feed at `https://techcrunch.com/feed/` and give me
> the titles and one-sentence summaries of the 5 most recent articles.

**Quality notes:**
- Setting `limit` to 5–10 produces faster responses and cleaner demo output.
- The `summary` field contains the RSS item's `<description>` tag, which may be
  plain text or HTML depending on the publisher.

**Known limitations:**
- RSS feeds that require authentication (behind a paywall) will return an HTTP error
  or an empty feed; use only publicly accessible feeds in demos.
- `published` is returned as a raw date string in the format used by the publisher;
  no normalisation is applied.

**When to customise:**
- Replace the feed URL with the client's preferred industry publication or internal
  RSS feed (e.g. from their CMS, blog platform, or Jira release notes).
- Reduce `limit` for quick demos; increase to 50 for a batch ingestion showcase.

---

### 4.2 Competitor product update feed

**Quality:** ✅ Production-ready

**Use case:** Product or competitive intelligence demo — monitor a competitor's
changelog or release notes.

**Request body:**
```json
{
  "url": "https://competitor.example.com/changelog/feed.xml",
  "limit": 15
}
```

**Prompt guidance (MCP transport):**
> Fetch the last 15 entries from the changelog RSS feed at
> `https://competitor.example.com/changelog/feed.xml`.  Group them by month and
> highlight any entries that mention pricing or security changes.

**Quality notes:**
- Changelog feeds typically have clean, structured summaries — ideal for demo use.
- Many SaaS products publish Atom feeds at `/changelog.xml`, `/releases.atom`, or
  `/feed.xml`; try these paths if the exact URL is unknown.

**Known limitations:**
- If the competitor does not publish an RSS/Atom feed, this tool cannot be used;
  switch to `POST /scrape/links` to discover recent articles manually.

**When to customise:**
- Replace the URL with the actual competitor changelog feed.
- Adjust the `limit` based on desired history depth.

---

### 4.3 Internal knowledge base feed

**Quality:** 🔧 Requires customisation

**Use case:** Internal tooling or knowledge management demo — surface recent updates
from a team wiki, Confluence space, or internal blog.

**Request body:**
```json
{
  "url": "https://wiki.internal.example.com/feed.xml",
  "limit": 20
}
```

**Prompt guidance (MCP transport):**
> Parse the internal wiki feed at `https://wiki.internal.example.com/feed.xml`
> and list all pages updated in the last 7 days with their author and a one-line
> description.

**Quality notes:**
- Many internal wikis (Confluence, Notion, Outline) support RSS/Atom export.
- `published` dates allow downstream filtering for recency without extra API calls.

**Known limitations:**
- Internal feeds are only reachable if the MCP server is deployed on the same
  network as the wiki; ensure network connectivity before demoing this use case.
- Confluence RSS feeds may include boilerplate HTML in the `summary` field;
  instruct the model to strip HTML when summarising.

**When to customise:**
- Replace the feed URL with the client's actual wiki or knowledge base feed URL.
- Adjust `limit` to cover the desired lookback period.
- If the feed requires HTTP Basic authentication, this is not supported by the
  current scraper implementation; request a code extension.
