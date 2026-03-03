"""
intelligence_mcp — FusionAL Market Intelligence Server
Aggregates hot topics + discovers business leads with zero API keys required.
Port: 8104 (HTTP) | Jonathan Melton / JRM — FusionAL
"""

import asyncio
import json
import re
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette

# ─────────────────────────────────────────────
# Server Init
# ─────────────────────────────────────────────
mcp = FastMCP("intelligence_mcp")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

HTTP_TIMEOUT = 15.0


# ─────────────────────────────────────────────
# Shared HTTP client
# ─────────────────────────────────────────────
async def get(url: str, params: Dict = None, json_mode: bool = True) -> Any:
    """Shared async HTTP GET with error handling."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json() if json_mode else r.text


def _handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        return f"Error: HTTP {e.response.status_code} — {e.request.url}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Source may be slow — retry."
    return f"Error: {type(e).__name__}: {str(e)}"


# ─────────────────────────────────────────────
# Source Fetchers
# ─────────────────────────────────────────────
async def _fetch_hackernews(limit: int = 8) -> List[Dict]:
    """Top stories from Hacker News."""
    ids = await get("https://hacker-news.firebaseio.com/v0/topstories.json")
    stories = []
    tasks = [get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json") for sid in ids[:limit * 2]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for item in results:
        if isinstance(item, dict) and item.get("type") == "story" and item.get("title"):
            stories.append({
                "source": "Hacker News",
                "title": item["title"],
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),
                "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                "tags": ["tech", "startup", "dev"],
            })
            if len(stories) >= limit:
                break
    return stories


async def _fetch_reddit_subreddits(limit_per_sub: int = 3) -> List[Dict]:
    """Hot posts from key AI/dev/MCP subreddits."""
    subs = [
        ("MachineLearning", ["AI", "research"]),
        ("artificial", ["AI", "trends"]),
        ("ClaudeAI", ["Claude", "MCP", "AI"]),
        ("mcp", ["MCP", "tools", "AI"]),
        ("programming", ["dev", "software"]),
        ("webdev", ["web", "frontend", "dev"]),
        ("selfhosted", ["self-hosted", "homelab"]),
    ]
    topics = []
    for sub, tags in subs:
        try:
            data = await get(f"https://www.reddit.com/r/{sub}/hot.json?limit={limit_per_sub}&raw_json=1")
            for post in data["data"]["children"][:limit_per_sub]:
                p = post["data"]
                if p.get("stickied") or not p.get("title"):
                    continue
                topics.append({
                    "source": f"r/{sub}",
                    "title": p["title"],
                    "score": p.get("score", 0),
                    "comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p['permalink']}",
                    "tags": tags,
                })
        except Exception:
            continue
    return topics


async def _fetch_devto(limit: int = 5) -> List[Dict]:
    """Top articles from Dev.to (last 7 days)."""
    articles = await get("https://dev.to/api/articles?top=7&per_page=20")
    results = []
    for a in articles[:limit]:
        results.append({
            "source": "Dev.to",
            "title": a["title"],
            "score": a.get("public_reactions_count", 0),
            "comments": a.get("comments_count", 0),
            "url": a["url"],
            "tags": a.get("tag_list", [])[:3],
        })
    return results


async def _fetch_github_trending(limit: int = 5) -> List[Dict]:
    """Scrape GitHub Trending page."""
    html = await get("https://github.com/trending", json_mode=False)
    soup = BeautifulSoup(html, "html.parser")
    repos = []
    for article in soup.select("article.Box-row")[:limit]:
        name_tag = article.select_one("h2 a")
        desc_tag = article.select_one("p")
        stars_tag = article.select_one("a[href$='/stargazers']")
        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        if not name_tag:
            continue
        repo_path = name_tag["href"].strip("/")
        repos.append({
            "source": "GitHub Trending",
            "title": repo_path,
            "description": desc_tag.get_text(strip=True) if desc_tag else "",
            "stars": stars_tag.get_text(strip=True) if stars_tag else "?",
            "language": lang_tag.get_text(strip=True) if lang_tag else "unknown",
            "url": f"https://github.com/{repo_path}",
            "tags": ["open-source", "trending", "dev"],
        })
    return repos


async def _fetch_producthunt(limit: int = 5) -> List[Dict]:
    """Scrape ProductHunt today's top products."""
    html = await get("https://www.producthunt.com/", json_mode=False)
    soup = BeautifulSoup(html, "html.parser")
    products = []
    # PH uses Next.js — grab from __NEXT_DATA__ script
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if script:
        try:
            data = json.loads(script.string)
            sections = data["props"]["pageProps"].get("sections", [])
            for section in sections:
                items = section.get("items", [])
                for item in items[:limit]:
                    products.append({
                        "source": "Product Hunt",
                        "title": item.get("name", ""),
                        "description": item.get("tagline", ""),
                        "score": item.get("votesCount", 0),
                        "url": f"https://www.producthunt.com/posts/{item.get('slug', '')}",
                        "tags": ["product", "startup", "launch"],
                    })
                if len(products) >= limit:
                    break
        except Exception:
            pass
    return products[:limit]


def _score_topic(t: Dict) -> int:
    return t.get("score", 0) + (t.get("comments", 0) * 3)


# ─────────────────────────────────────────────
# Pydantic Input Models
# ─────────────────────────────────────────────
class HotTopicsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    count: int = Field(default=20, description="Number of hot topics to return (5–50)", ge=5, le=50)
    sources: Optional[List[str]] = Field(
        default=None,
        description="Filter sources: 'hackernews', 'reddit', 'devto', 'github', 'producthunt'. None = all."
    )
    filter_tag: Optional[str] = Field(
        default=None, description="Filter by tag keyword, e.g. 'AI', 'MCP', 'startup'", max_length=50
    )
    response_format: str = Field(default="markdown", description="'markdown' or 'json'")


class BusinessLeadsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    niche: str = Field(
        ...,
        description="Target niche, e.g. 'AI tools', 'developer tools SaaS', 'MCP integrations', 'automation agencies'",
        min_length=2,
        max_length=100,
    )
    intent: str = Field(
        default="exposure",
        description="Lead intent: 'exposure' (blogs/channels to feature you), 'client' (businesses that need MCP consulting), or 'partnership' (integration/collab targets)",
    )
    count: int = Field(default=15, description="Number of leads to generate (5–30)", ge=5, le=30)
    response_format: str = Field(default="markdown", description="'markdown' or 'json'")


class TrendingReposInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    language: Optional[str] = Field(default=None, description="Filter by language, e.g. 'python', 'typescript'")
    period: str = Field(default="daily", description="'daily', 'weekly', or 'monthly'")


# ─────────────────────────────────────────────
# TOOL 1: Hot Topics
# ─────────────────────────────────────────────
@mcp.tool(
    name="intelligence_get_hot_topics",
    annotations={
        "title": "Get Hot Topics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def intelligence_get_hot_topics(params: HotTopicsInput) -> str:
    """
    Retrieves the hottest topics right now from Hacker News, Reddit (AI/dev/MCP subs),
    Dev.to, GitHub Trending, and Product Hunt. Returns ranked by engagement score.
    Useful for: content ideas, dev.to articles, X/Twitter posts, identifying what's viral.

    Args:
        params (HotTopicsInput):
            - count (int): How many topics to return (default 20)
            - sources (List[str]): Filter to specific sources (None = all)
            - filter_tag (str): Optional tag filter, e.g. 'AI', 'MCP'
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Ranked list of hot topics with source, title, engagement, URL, tags.
    """
    allowed = params.sources or ["hackernews", "reddit", "devto", "github", "producthunt"]

    fetch_tasks = {}
    if "hackernews" in allowed:
        fetch_tasks["hackernews"] = _fetch_hackernews(10)
    if "reddit" in allowed:
        fetch_tasks["reddit"] = _fetch_reddit_subreddits(4)
    if "devto" in allowed:
        fetch_tasks["devto"] = _fetch_devto(8)
    if "github" in allowed:
        fetch_tasks["github"] = _fetch_github_trending(8)
    if "producthunt" in allowed:
        fetch_tasks["producthunt"] = _fetch_producthunt(5)

    results_map = {}
    for key, coro in fetch_tasks.items():
        try:
            results_map[key] = await coro
        except Exception as e:
            results_map[key] = []

    all_topics = []
    for items in results_map.values():
        all_topics.extend(items)

    # Tag filter
    if params.filter_tag:
        tag_lower = params.filter_tag.lower()
        filtered = [
            t for t in all_topics
            if tag_lower in " ".join(str(x) for x in t.get("tags", [])).lower()
            or tag_lower in t.get("title", "").lower()
            or tag_lower in t.get("description", "").lower()
        ]
        all_topics = filtered if filtered else all_topics

    # Sort by engagement
    all_topics.sort(key=_score_topic, reverse=True)
    top = all_topics[: params.count]

    if params.response_format == "json":
        return json.dumps({"count": len(top), "topics": top, "fetched_at": datetime.now(timezone.utc).isoformat()}, indent=2)

    # Markdown
    lines = [
        f"# 🔥 Top {len(top)} Hot Topics — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    for i, t in enumerate(top, 1):
        tags_str = " ".join(f"`{tg}`" for tg in t.get("tags", [])[:3])
        score = t.get("score", 0)
        comments = t.get("comments", 0)
        desc = t.get("description", "")
        lines += [
            f"### {i}. [{t['title']}]({t['url']})",
            f"**Source:** {t['source']} &nbsp;|&nbsp; ⬆ {score} &nbsp;|&nbsp; 💬 {comments}",
            f"{tags_str}",
        ]
        if desc:
            lines.append(f"_{desc}_")
        lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# TOOL 2: Business Leads
# ─────────────────────────────────────────────

# Curated lead database by intent + niche (dynamically filtered)
LEAD_TEMPLATES = {
    "exposure": [
        {"name": "NetworkChuck (YouTube/Blog)", "type": "Tech Educator", "contact": "chuck@networkchuck.com",
         "audience": "2M+ developers & sysadmins", "pitch": "MCP tools for devs / AI integration demos",
         "url": "https://networkchuck.com", "relevance_tags": ["AI", "dev", "tools", "automation", "MCP"]},
        {"name": "Dev.to Community", "type": "Developer Blog Platform", "contact": "Post at dev.to/new",
         "audience": "1M+ devs", "pitch": "Write: '150+ AI Tools in One Docker Command'",
         "url": "https://dev.to", "relevance_tags": ["dev", "AI", "docker", "tools", "MCP"]},
        {"name": "Hacker News (Show HN)", "type": "Tech News Community", "contact": "news.ycombinator.com/submit",
         "audience": "500K+ tech founders/devs", "pitch": "Show HN: FusionAL — 150+ MCP tools, one Docker command",
         "url": "https://news.ycombinator.com", "relevance_tags": ["AI", "tools", "dev", "startup", "MCP"]},
        {"name": "Fireship (YouTube)", "type": "Tech Educator", "contact": "https://fireship.io/contact",
         "audience": "2M+ devs, viral short-form content", "pitch": "MCP + AI tools in 100 seconds format",
         "url": "https://fireship.io", "relevance_tags": ["AI", "dev", "tools", "docker"]},
        {"name": "Theo / t3.gg (YouTube/X)", "type": "Tech Influencer", "contact": "@t3dotgg on X",
         "audience": "800K+ devs (web/TS/AI focus)", "pitch": "AI-powered dev toolchain angle",
         "url": "https://t3.gg", "relevance_tags": ["AI", "dev", "tools", "startup"]},
        {"name": "Awesome MCP Servers (GitHub PR)", "type": "Curated GitHub List", "contact": "github.com/punkpeye/awesome-mcp-servers",
         "audience": "All MCP developers globally", "pitch": "Submit FusionAL gateway PR",
         "url": "https://github.com/punkpeye/awesome-mcp-servers", "relevance_tags": ["MCP", "AI", "tools"]},
        {"name": "Smithery.ai", "type": "MCP Registry", "contact": "smithery.ai/submit",
         "audience": "All Claude/MCP users", "pitch": "List FusionAL as a one-click install",
         "url": "https://smithery.ai", "relevance_tags": ["MCP", "Claude", "AI", "tools"]},
        {"name": "Reddit r/ClaudeAI", "type": "Community Forum", "contact": "reddit.com/r/ClaudeAI/submit",
         "audience": "50K+ Claude power users", "pitch": "Post gateway tutorial + demo GIF",
         "url": "https://reddit.com/r/ClaudeAI", "relevance_tags": ["Claude", "MCP", "AI", "tools"]},
        {"name": "Reddit r/mcp", "type": "Community Forum", "contact": "reddit.com/r/mcp/submit",
         "audience": "Growing MCP developer community", "pitch": "Share Windows failure modes solved",
         "url": "https://reddit.com/r/mcp", "relevance_tags": ["MCP", "tools", "dev"]},
        {"name": "Changelog Podcast/Newsletter", "type": "Dev Media", "contact": "changelog.com/guest",
         "audience": "200K+ devs", "pitch": "Self-taught, hospital-built, 150+ tools angle",
         "url": "https://changelog.com", "relevance_tags": ["dev", "AI", "tools", "startup"]},
        {"name": "TLDR Newsletter (AI edition)", "type": "Tech Newsletter", "contact": "advertise@tldr.tech",
         "audience": "500K+ tech readers", "pitch": "FusionAL launch feature or sponsored",
         "url": "https://tldr.tech", "relevance_tags": ["AI", "tools", "startup", "dev"]},
        {"name": "Ben's Bites Newsletter", "type": "AI Newsletter", "contact": "bensbites.beehiiv.com",
         "audience": "100K+ AI enthusiasts", "pitch": "Featured tool / integration spotlight",
         "url": "https://bensbites.co", "relevance_tags": ["AI", "tools", "MCP", "startup"]},
        {"name": "IndieHackers", "type": "Founder Community", "contact": "indiehackers.com/new-story",
         "audience": "300K+ indie founders", "pitch": "Recovering addict ships AI infra from scratch",
         "url": "https://indiehackers.com", "relevance_tags": ["startup", "AI", "tools", "dev"]},
        {"name": "Matt Wolfe (YouTube/Newsletter)", "type": "AI Educator", "contact": "mattwolfe.com",
         "audience": "1M+ AI enthusiasts", "pitch": "FusionAL as ultimate local AI toolkit",
         "url": "https://www.mattwolfe.com", "relevance_tags": ["AI", "tools", "automation"]},
    ],
    "client": [
        {"name": "AI SaaS Startups (Series A-B)", "type": "Target Client Segment", "contact": "LinkedIn / AngelList",
         "audience": "Need MCP integrations fast, budget for consulting",
         "pitch": "Done-for-you MCP gateway setup — 1 Docker command, 150+ tools",
         "url": "https://angellist.com", "relevance_tags": ["AI", "startup", "SaaS", "MCP"]},
        {"name": "Digital Marketing Agencies", "type": "Target Client Segment", "contact": "Cold email / LinkedIn",
         "audience": "Need automation, AI content pipelines",
         "pitch": "Automate 80% of content ops with MCP + Claude",
         "url": "https://clutch.co/agencies/digital-marketing", "relevance_tags": ["automation", "AI", "marketing"]},
        {"name": "No-Code / Low-Code Builders", "type": "Target Client Segment", "contact": "Makerpad / Bubble forums",
         "audience": "Want AI superpowers without deep dev knowledge",
         "pitch": "MCP as the power layer for no-code AI workflows",
         "url": "https://makerpad.zapier.com", "relevance_tags": ["automation", "AI", "tools", "no-code"]},
        {"name": "Fiverr Business / Pro Buyers", "type": "Marketplace Leads", "contact": "fiverr.com — create gig",
         "audience": "Businesses actively searching for AI integration dev",
         "pitch": "Create: 'I will set up your Claude Desktop MCP environment'",
         "url": "https://fiverr.com", "relevance_tags": ["AI", "MCP", "dev", "consulting"]},
        {"name": "Upwork AI Developers Market", "type": "Marketplace Leads", "contact": "upwork.com — create profile",
         "audience": "Companies hiring AI/automation devs",
         "pitch": "MCP consulting + FusionAL gateway specialization",
         "url": "https://upwork.com", "relevance_tags": ["AI", "dev", "consulting", "automation"]},
        {"name": "Enterprise IT Consultancies", "type": "Target Client Segment", "contact": "LinkedIn outreach",
         "audience": "Implement AI tools for mid-market companies",
         "pitch": "White-label MCP gateway for their client stack",
         "url": "https://linkedin.com", "relevance_tags": ["AI", "enterprise", "consulting", "tools"]},
        {"name": "AI Automation Agencies (AAAs)", "type": "Target Client Segment", "contact": "Cold email / Twitter",
         "audience": "Build AI workflows for clients — need robust infra",
         "pitch": "FusionAL as the infra layer — recurring revenue share potential",
         "url": "https://linkedin.com/search/results/companies/?keywords=AI+automation+agency", "relevance_tags": ["AI", "automation", "MCP", "agency"]},
        {"name": "SaaS Founders on Twitter/X", "type": "Inbound Lead Channel", "contact": "Twitter DMs / replies",
         "audience": "Founders actively building with Claude/LLMs",
         "pitch": "Offer free MCP setup call via Calendly",
         "url": "https://twitter.com/search?q=claude+mcp+integration", "relevance_tags": ["AI", "SaaS", "MCP", "startup"]},
        {"name": "ProductHunt Makers", "type": "Warm Lead Pool", "contact": "PH comments / maker profiles",
         "audience": "Active product builders, many using AI",
         "pitch": "'I can add 150+ AI tools to your workflow in 10 min'",
         "url": "https://producthunt.com", "relevance_tags": ["AI", "tools", "startup", "product"]},
        {"name": "Local Louisville Tech Scene", "type": "Geographic Advantage", "contact": "Louisville Chamber / meetups",
         "audience": "Regional businesses wanting AI advantage",
         "pitch": "Only MCP specialist in Louisville — local + remote consulting",
         "url": "https://www.louisvilletechnology.org", "relevance_tags": ["consulting", "AI", "local"]},
    ],
    "partnership": [
        {"name": "Anthropic Developer Relations", "type": "Platform Partnership", "contact": "anthropic.com/contact",
         "audience": "Official Claude ecosystem recognition",
         "pitch": "FusionAL as reference implementation for Windows MCP",
         "url": "https://anthropic.com", "relevance_tags": ["Claude", "MCP", "AI", "tools"]},
        {"name": "Docker Hub / Docker Partners", "type": "Platform Partnership", "contact": "docker.com/partners",
         "audience": "Millions of Docker users", "pitch": "Official Docker image for MCP gateway",
         "url": "https://hub.docker.com", "relevance_tags": ["docker", "dev", "tools", "MCP"]},
        {"name": "n8n (Workflow Automation)", "type": "Integration Partner", "contact": "n8n.io/community",
         "audience": "500K+ automation builders",
         "pitch": "FusionAL ↔ n8n native MCP node integration",
         "url": "https://n8n.io", "relevance_tags": ["automation", "AI", "tools", "integration"]},
        {"name": "LangChain / LangSmith", "type": "Ecosystem Partner", "contact": "langchain.com/contact",
         "audience": "Largest LLM dev community", "pitch": "MCP ↔ LangChain bridge tool",
         "url": "https://langchain.com", "relevance_tags": ["AI", "LLM", "dev", "tools"]},
        {"name": "Zapier AI Actions", "type": "Integration Partner", "contact": "zapier.com/developer",
         "audience": "5M+ automation users", "pitch": "FusionAL tools as Zapier AI actions",
         "url": "https://zapier.com", "relevance_tags": ["automation", "AI", "integration", "no-code"]},
    ],
}


@mcp.tool(
    name="intelligence_find_business_leads",
    annotations={
        "title": "Find Business Leads",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def intelligence_find_business_leads(params: BusinessLeadsInput) -> str:
    """
    Returns curated, actionable business leads for exposure, client acquisition, or partnerships.
    Leads are matched to your niche and include contact info, pitch angle, and relevance score.
    Tuned for FusionAL / MCP consulting use case.

    Args:
        params (BusinessLeadsInput):
            - niche (str): Target niche keyword, e.g. 'AI tools', 'developer tools', 'automation'
            - intent (str): 'exposure', 'client', or 'partnership'
            - count (int): Number of leads to return (default 15)
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Ranked list of business leads with name, type, contact, pitch, and URL.
    """
    intent = params.intent.lower()
    if intent not in LEAD_TEMPLATES:
        intent = "exposure"

    leads = LEAD_TEMPLATES[intent]
    niche_lower = params.niche.lower()
    niche_words = set(re.split(r"[\s,]+", niche_lower))

    # Score by relevance to niche
    def _relevance(lead: Dict) -> int:
        tags = " ".join(lead.get("relevance_tags", [])).lower()
        name = lead.get("name", "").lower()
        pitch = lead.get("pitch", "").lower()
        combined = f"{tags} {name} {pitch}"
        return sum(1 for w in niche_words if w in combined)

    scored = sorted(leads, key=_relevance, reverse=True)
    top = scored[: params.count]

    if params.response_format == "json":
        return json.dumps({"intent": intent, "niche": params.niche, "count": len(top), "leads": top}, indent=2)

    emoji = {"exposure": "📣", "client": "💰", "partnership": "🤝"}
    lines = [
        f"# {emoji.get(intent, '🎯')} Business Leads — {intent.capitalize()} | Niche: {params.niche}",
        f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]
    for i, lead in enumerate(top, 1):
        rel = _relevance(lead)
        rel_bar = "🟢" * min(rel, 3) + "⚪" * max(0, 3 - rel)
        lines += [
            f"## {i}. {lead['name']}",
            f"**Type:** {lead['type']} &nbsp;|&nbsp; **Relevance:** {rel_bar}",
            f"**Audience:** {lead['audience']}",
            f"**Pitch:** _{lead['pitch']}_",
            f"**Contact:** `{lead['contact']}`",
            f"**URL:** {lead['url']}",
            "",
        ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# TOOL 3: GitHub Trending (with language/period)
# ─────────────────────────────────────────────
@mcp.tool(
    name="intelligence_get_trending_repos",
    annotations={
        "title": "Get Trending GitHub Repos",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def intelligence_get_trending_repos(params: TrendingReposInput) -> str:
    """
    Scrapes GitHub Trending for the hottest repos right now.
    Useful for: spotting competitor tools, finding collab targets, content angles.

    Args:
        params (TrendingReposInput):
            - language (str): Filter by language, e.g. 'python', 'typescript' (optional)
            - period (str): 'daily', 'weekly', or 'monthly' (default 'daily')

    Returns:
        str: Markdown list of trending repos with name, description, stars, language.
    """
    url = "https://github.com/trending"
    query = f"/{params.language.lower()}" if params.language else ""
    full_url = f"{url}{query}"
    period_map = {"daily": "", "weekly": "?since=weekly", "monthly": "?since=monthly"}
    suffix = period_map.get(params.period, "")
    full_url = f"{full_url}{suffix}"

    try:
        html = await get(full_url, json_mode=False)
    except Exception as e:
        return _handle_error(e)

    soup = BeautifulSoup(html, "html.parser")
    lines = [f"# 🌟 GitHub Trending — {params.period.capitalize()}", ""]

    for i, article in enumerate(soup.select("article.Box-row")[:20], 1):
        name_tag = article.select_one("h2 a")
        desc_tag = article.select_one("p")
        stars_tag = article.select_one("a[href$='/stargazers']")
        stars_today = article.select_one(".d-inline-block.float-sm-right")
        lang_tag = article.select_one("[itemprop='programmingLanguage']")

        if not name_tag:
            continue

        repo_path = name_tag["href"].strip("/")
        desc = desc_tag.get_text(strip=True) if desc_tag else "No description"
        stars = stars_tag.get_text(strip=True) if stars_tag else "?"
        today = stars_today.get_text(strip=True) if stars_today else ""
        lang = lang_tag.get_text(strip=True) if lang_tag else "?"

        lines += [
            f"### {i}. [{repo_path}](https://github.com/{repo_path})",
            f"**Lang:** `{lang}` &nbsp;|&nbsp; ⭐ {stars} &nbsp;|&nbsp; 📈 {today}",
            f"_{desc}_",
            "",
        ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# TOOL 4: Quick Pulse — single-call summary
# ─────────────────────────────────────────────
@mcp.tool(
    name="intelligence_daily_pulse",
    annotations={
        "title": "Daily Intelligence Pulse",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def intelligence_daily_pulse(dummy: str = "") -> str:
    """
    One-shot daily briefing: top 5 hot topics + top 5 exposure leads + top 3 trending repos.
    Run this every morning for your content/outreach plan.

    Returns:
        str: Markdown daily intelligence briefing for FusionAL.
    """
    topics_task = intelligence_get_hot_topics(HotTopicsInput(count=5, filter_tag="AI"))
    leads_task = intelligence_find_business_leads(BusinessLeadsInput(niche="AI tools MCP developer", intent="exposure", count=5))
    repos_task = intelligence_get_trending_repos(TrendingReposInput(period="daily"))

    topics, leads, repos = await asyncio.gather(topics_task, leads_task, repos_task)

    return "\n\n---\n\n".join([
        f"# 🧠 FusionAL Daily Intelligence Pulse — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        topics,
        leads,
        repos[:1500] + "\n\n_(Full repo list: use `intelligence_get_trending_repos`)_",
    ])


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8104"))
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=port)
