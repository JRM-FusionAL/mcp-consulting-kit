from pydantic import BaseModel
from typing import Optional
from scraper import extract_article, extract_links, extract_tables
import feedparser

class ScrapeRequest(BaseModel):
    url: str

class RSSRequest(BaseModel):
    url: str
    limit: int = 20

def scrape_article(payload: ScrapeRequest):
    return extract_article(payload.url)

def scrape_links(payload: ScrapeRequest):
    return {"url": payload.url, "links": extract_links(payload.url)}

def scrape_tables(payload: ScrapeRequest):
    return {"url": payload.url, "tables": extract_tables(payload.url)}

def parse_rss(payload: RSSRequest):
    feed = feedparser.parse(payload.url)
    entries = []
    for entry in feed.entries[: payload.limit]:
        entries.append(
            {
                "title": getattr(entry, "title", ""),
                "link": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", ""),
                "published": getattr(entry, "published", ""),
            }
        )
    return {"feed_title": getattr(feed.feed, "title", ""), "entries": entries}
