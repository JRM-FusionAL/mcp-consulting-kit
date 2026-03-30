"""
Streamable HTTP MCP transport — GitHub MCP Safe

Exposes rate-limited GitHub operations as MCP tools.
Clients connect to: http://localhost:8105/mcp
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp_tools import (
    list_issues,
    create_issue,
    bulk_analyze_issues,
    get_rate_limit_status,
)

mcp = FastMCP(
    "github-mcp-safe",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

@mcp.tool(name="list_issues", description="List GitHub issues with safe rate limiting.")
async def _list_issues(repo: str, state: str = "open", labels: str = "", per_page: int = 30) -> dict:
    return await list_issues(repo=repo, state=state, labels=labels or None, per_page=per_page)

@mcp.tool(name="create_issue", description="Create a GitHub issue with rate limiting.")
async def _create_issue(repo: str, title: str, body: str = "", labels: str = "") -> dict:
    return await create_issue(repo=repo, title=title, body=body or None,
                               labels=labels.split(",") if labels else None)

@mcp.tool(name="bulk_analyze_issues",
          description="Analyze multiple issues in ONE GraphQL call — 97% fewer API requests.")
async def _bulk_analyze(repo: str, max_issues: int = 10) -> dict:
    return await bulk_analyze_issues(repo=repo, max_issues=max_issues)

@mcp.tool(name="get_rate_limit_status",
          description="Check current GitHub API rate limits and local sliding window metrics.")
async def _rate_limit_status() -> dict:
    return await get_rate_limit_status()
