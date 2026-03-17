#!/usr/bin/env python
"""
Pull latest market intelligence from intelligence_mcp
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path so we can import intelligence_mcp
sys.path.insert(0, str(Path(__file__).parent))

from intelligence_mcp import (
    intelligence_get_hot_topics,
    intelligence_find_business_leads,
    intelligence_get_trending_repos,
    HotTopicsInput,
    BusinessLeadsInput,
    TrendingReposInput,
)

async def main():
    print("\n" + "="*70)
    print("🧠 FUSIONAL DAILY INTELLIGENCE PULSE — 2026-03-17")
    print("="*70)
    
    # Get hot topics
    print("\n\n🔥 TOP HOT TOPICS (AI)\n" + "─"*70)
    topics = await intelligence_get_hot_topics(
        HotTopicsInput(count=5, filter_tag="AI", response_format="markdown")
    )
    print(topics)
    
    # Get business leads
    print("\n\n💰 BUSINESS LEADS (EXPOSURE)\n" + "─"*70)
    leads = await intelligence_find_business_leads(
        BusinessLeadsInput(
            niche="AI tools MCP developer",
            intent="exposure",
            count=5,
            response_format="markdown"
        )
    )
    print(leads)
    
    # Get trending repos
    print("\n\n🌟 TRENDING REPOSITORIES (DAILY)\n" + "─"*70)
    repos = await intelligence_get_trending_repos(TrendingReposInput(period="daily"))
    print(repos[:2000])  # Truncate to first 2000 chars

if __name__ == "__main__":
    asyncio.run(main())
