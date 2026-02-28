"""
Streamable HTTP MCP transport — API Integration Hub

Exposes Slack, GitHub, and Stripe as MCP tools.
Clients connect to: http://localhost:8102/mcp
"""

from mcp.server.fastmcp import FastMCP
from mcp_tools import (
    SlackMessageRequest,
    GitHubIssueRequest,
    StripeCustomerLookupRequest,
    send_slack_message,
    create_issue_and_optionally_notify,
    lookup_stripe_customer,
)

mcp = FastMCP("api-integration-hub")


@mcp.tool(
    name="slack_send",
    description="Send a message to a Slack channel.",
)
def slack_send(channel: str, text: str) -> dict:
    return send_slack_message(SlackMessageRequest(channel=channel, text=text))


@mcp.tool(
    name="github_create_issue",
    description="Create a GitHub issue in any repo. Optionally notify a Slack channel.",
)
def github_create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str = "",
    notify_slack_channel: str = "",
) -> dict:
    return create_issue_and_optionally_notify(
        GitHubIssueRequest(
            owner=owner,
            repo=repo,
            title=title,
            body=body if body else None,
            notify_slack_channel=notify_slack_channel if notify_slack_channel else None,
        )
    )


@mcp.tool(
    name="stripe_customer_lookup",
    description="Look up a Stripe customer — returns profile, charge history, and active subscriptions.",
)
def stripe_customer_lookup(customer_id: str) -> dict:
    return lookup_stripe_customer(StripeCustomerLookupRequest(customer_id=customer_id))
