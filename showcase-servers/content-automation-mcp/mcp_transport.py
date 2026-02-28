"""
Streamable HTTP MCP transport — Content Automation MCP

Exposes web scraping and RSS parsing as MCP tools.
Clients connect to: http://localhost:8103/mcp
"""

from mcp.server.fastmcp import FastMCP
from mcp_tools import (
    ScrapeRequest,
    RSSRequest,
    scrape_article,
    scrape_links,
    scrape_tables,
    parse_rss,
)

mcp = FastMCP("content-automation-mcp")


@mcp.tool(
    name="scrape_article",
    description="Extract the main article text and metadata from any URL.",
)
def scrape_article_tool(url: str) -> dict:
    """
    Args:
        url: Full URL of the page to scrape. Example: 'https://example.com/blog/post'
    """
    return scrape_article(ScrapeRequest(url=url))


@mcp.tool(
    name="scrape_links",
    description="Extract all hyperlinks from a page.",
)
def scrape_links_tool(url: str) -> dict:
    """
    Args:
        url: Full URL of the page to scrape.
    """
    return scrape_links(ScrapeRequest(url=url))


@mcp.tool(
    name="scrape_tables",
    description="Extract all HTML tables from a page as structured data.",
)
def scrape_tables_tool(url: str) -> dict:
    """
    Args:
        url: Full URL of the page containing tables.
    """
    return scrape_tables(ScrapeRequest(url=url))


@mcp.tool(
    name="parse_rss",
    description="Fetch and parse an RSS feed. Returns entries with title, link, summary, and date.",
)
def parse_rss_tool(url: str, limit: int = 20) -> dict:
    """
    Args:
        url: RSS feed URL. Example: 'https://news.ycombinator.com/rss'
        limit: Max number of entries to return (default 20).
    """
    return parse_rss(RSSRequest(url=url, limit=limit))
