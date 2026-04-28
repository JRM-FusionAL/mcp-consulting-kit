"""
mcp_tools.py — GitHub MCP Safe (showcase server)

Copies core logic from github-mcp-safe standalone repo.
Self-contained — no cross-repo imports.
"""

import os
import asyncio
import time
import random
import logging
from collections import deque
from dataclasses import dataclass
from typing import Optional
import httpx

logger = logging.getLogger("github-mcp-safe.tools")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"

# --- Rate limiter ---

@dataclass
class RateLimitMetrics:
    total_requests: int = 0
    requests_last_minute: int = 0
    requests_last_hour: int = 0
    total_wait_time: float = 0.0
    retries: int = 0
    rate_limit_hits: int = 0
    successful_requests: int = 0

    def success_rate(self) -> float:
        return (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0.0

class GitHubRateLimiter:
    def __init__(self):
        self.minute_window: deque = deque()
        self.hour_window: deque = deque()
        self._lock = asyncio.Lock()
        self.metrics = RateLimitMetrics()
        self.rpm_limit = 50
        self.rph_limit = 4000

    def _clean(self, window, cutoff):
        while window and window[0] < cutoff:
            window.popleft()

    async def wait_if_needed(self):
        async with self._lock:
            now = time.time()
            self._clean(self.minute_window, now - 60)
            self._clean(self.hour_window, now - 3600)
            if len(self.minute_window) >= self.rpm_limit:
                wait = 60 - (now - self.minute_window[0]) + 0.1
                self.metrics.total_wait_time += wait
                self.metrics.rate_limit_hits += 1
                await asyncio.sleep(wait)
                now = time.time()
            self.minute_window.append(now)
            self.hour_window.append(now)
            self.metrics.total_requests += 1

    def get_metrics(self) -> RateLimitMetrics:
        now = time.time()
        self._clean(self.minute_window, now - 60)
        self._clean(self.hour_window, now - 3600)
        self.metrics.requests_last_minute = len(self.minute_window)
        self.metrics.requests_last_hour = len(self.hour_window)
        return self.metrics

_limiter = GitHubRateLimiter()

# --- GitHub API client ---

def _headers():
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

async def _get(path: str, params: dict = None) -> any:
    await _limiter.wait_if_needed()
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{GITHUB_API}{path}", headers=_headers(), params=params, timeout=15)
        r.raise_for_status()
        _limiter.metrics.successful_requests += 1
        return r.json()

async def _post(path: str, json: dict) -> any:
    await _limiter.wait_if_needed()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{GITHUB_API}{path}", headers=_headers(), json=json, timeout=15)
        r.raise_for_status()
        _limiter.metrics.successful_requests += 1
        return r.json()

async def _graphql(query: str, variables: dict) -> any:
    await _limiter.wait_if_needed()
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.github.com/graphql",
            headers=_headers(),
            json={"query": query, "variables": variables},
            timeout=15,
        )
        r.raise_for_status()
        _limiter.metrics.successful_requests += 1
        return r.json().get("data", {})

# --- Tool implementations ---

async def list_issues(repo: str, state: str = "open",
                      labels: Optional[str] = None, per_page: int = 30) -> dict:
    params = {"state": state, "per_page": min(per_page, 100)}
    if labels:
        params["labels"] = labels
    issues = await _get(f"/repos/{repo}/issues", params=params)
    return {"repo": repo, "count": len(issues), "issues": issues}

async def create_issue(repo: str, title: str,
                       body: Optional[str] = None, labels: Optional[list] = None) -> dict:
    payload = {"title": title}
    if body:
        payload["body"] = body
    if labels:
        payload["labels"] = labels
    issue = await _post(f"/repos/{repo}/issues", json=payload)
    return {"number": issue["number"], "url": issue["html_url"], "title": issue["title"]}

async def bulk_analyze_issues(repo: str, max_issues: int = 10) -> dict:
    owner, repo_name = repo.split("/")
    query = """
    query($owner: String!, $repo: String!, $maxIssues: Int!) {
      repository(owner: $owner, name: $repo) {
        issues(first: $maxIssues, states: OPEN, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            number title body
            labels(first: 10) { nodes { name } }
            comments(first: 5) { totalCount }
            assignees(first: 5) { nodes { login } }
          }
        }
      }
    }"""
    data = await _graphql(query, {"owner": owner, "repo": repo_name, "maxIssues": max_issues})
    issues = data["repository"]["issues"]["nodes"]
    analyzed = []
    for issue in issues:
        analyzed.append({
            "number": issue["number"],
            "title": issue["title"],
            "suitable_for_ai": (
                len(issue.get("body") or "") > 100
                and len(issue["labels"]["nodes"]) > 0
                and len(issue["assignees"]["nodes"]) == 0
                and issue["comments"]["totalCount"] < 10
            ),
            "labels": [l["name"] for l in issue["labels"]["nodes"]],
            "comments_count": issue["comments"]["totalCount"],
        })
    return {"repo": repo, "analyzed_count": len(analyzed), "issues": analyzed}

async def get_rate_limit_status() -> dict:
    data = await _get("/rate_limit")
    metrics = _limiter.get_metrics()
    return {
        "github_api": data.get("resources", {}),
        "local_metrics": {
            "total_requests": metrics.total_requests,
            "requests_last_minute": metrics.requests_last_minute,
            "requests_last_hour": metrics.requests_last_hour,
            "total_wait_time_seconds": round(metrics.total_wait_time, 2),
            "retries": metrics.retries,
            "rate_limit_hits": metrics.rate_limit_hits,
            "success_rate": round(metrics.success_rate(), 2),
        },
    }
