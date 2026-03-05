from pydantic import BaseModel
from typing import Optional
from clients.slack_client import SlackClient
from clients.github_client import SafeGitHubClient
from clients.stripe_client import StripeClient

class SlackMessageRequest(BaseModel):
    channel: str
    text: str

class GitHubIssueRequest(BaseModel):
    owner: str
    repo: str
    title: str
    body: Optional[str] = None
    notify_slack_channel: Optional[str] = None

class StripeCustomerLookupRequest(BaseModel):
    customer_id: str

def send_slack_message(payload: SlackMessageRequest):
    client = SlackClient()
    return client.post_message(payload.channel, payload.text)

async def create_issue_and_optionally_notify(payload: GitHubIssueRequest):
    async with SafeGitHubClient() as gh:
        issue = await gh.post(
            f"/repos/{payload.owner}/{payload.repo}/issues",
            json={"title": payload.title, "body": payload.body or ""}
        )
    if payload.notify_slack_channel:
        slack = SlackClient()
        text = f"New GitHub issue created: {issue.get('html_url')}"
        slack.post_message(payload.notify_slack_channel, text)
    return issue

def lookup_stripe_customer(payload: StripeCustomerLookupRequest):
    stripe = StripeClient()
    customer = stripe.retrieve_customer(payload.customer_id)
    charges = stripe.list_charges(customer_id=payload.customer_id)
    subs = stripe.list_subscriptions(customer_id=payload.customer_id)
    return {
        "customer": customer,
        "charges": charges,
        "subscriptions": subs,
    }
