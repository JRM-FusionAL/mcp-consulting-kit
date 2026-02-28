"""
Streamable HTTP MCP transport layer for Business Intelligence MCP.

Wraps existing business logic in proper MCP protocol using FastMCP.
Mounts at /mcp on the FastAPI app — any MCP client can connect here.
"""

from mcp.server.fastmcp import FastMCP
from mcp_tools import NLQueryRequest, handle_nl_query

mcp = FastMCP("business-intelligence-mcp")


@mcp.tool(
    name="nl_query",
    description=(
        "Convert a natural language question into SQL and run it against the connected database. "
        "Returns the generated SQL and result rows. Read-only — SELECT/CTE queries only."
    ),
)
def nl_query(query: str, schema_hint: str = "") -> dict:
    payload = NLQueryRequest(
        query=query,
        schema_hint=schema_hint if schema_hint else None,
    )
    return handle_nl_query(payload)
