"""
News fetcher: RSS feeds (CoinDesk, Cointelegraph, CryptoSlate) + Alpha Vantage.
Deduplication by URL — same pattern as HKUDS/AI-Trader market_intel.py.
"""
import asyncio
import logging
import time
from typing import List, Dict
from urllib.parse import urlparse

import aiohttp
import feedparser

from trading_bot.config import config

log = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/",
    "https://decrypt.co/feed",
]

# In-memory cache: list of {title, url, summary, published, source}
_news_cache: List[Dict] = []
_last_fetch: float = 0.0
_seen_urls: set = set()


async def _fetch_rss(session: aiohttp.ClientSession, url: str) -> List[Dict]:
    items = []
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            text = await resp.text()
        feed = feedparser.parse(text)
        source = urlparse(url).netloc.replace("www.", "")
        for entry in feed.entries[:15]:
            link = entry.get("link", "")
            if link in _seen_urls:
                continue
            items.append({
                "title": entry.get("title", ""),
                "url": link,
                "summary": entry.get("summary", "")[:300],
                "published": entry.get("published", ""),
                "source": source,
            })
    except Exception as exc:
        log.warning("RSS fetch failed [%s]: %s", url, exc)
    return items


async def _fetch_alpha_vantage(session: aiohttp.ClientSession) -> List[Dict]:
    if not config.alpha_vantage_key:
        return []
    url = (
        "https://www.alphavantage.co/query"
        "?function=NEWS_SENTIMENT"
        "&topics=cryptocurrency,blockchain,financial_markets"
        f"&apikey={config.alpha_vantage_key}"
        "&limit=20"
    )
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
        items = []
        for article in data.get("feed", []):
            link = article.get("url", "")
            if link in _seen_urls:
                continue
            items.append({
                "title": article.get("title", ""),
                "url": link,
                "summary": article.get("summary", "")[:300],
                "published": article.get("time_published", ""),
                "source": article.get("source", "alphavantage"),
                "av_sentiment_score": float(article.get("overall_sentiment_score", 0)),
                "av_sentiment_label": article.get("overall_sentiment_label", "Neutral"),
            })
        return items
    except Exception as exc:
        log.warning("Alpha Vantage news fetch failed: %s", exc)
        return []


async def refresh_news() -> None:
    """Fetch all news sources and update the cache."""
    global _last_fetch, _news_cache
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_rss(session, url) for url in RSS_FEEDS]
        tasks.append(_fetch_alpha_vantage(session))
        results = await asyncio.gather(*tasks, return_exceptions=True)

    fresh: List[Dict] = []
    for batch in results:
        if isinstance(batch, list):
            fresh.extend(batch)

    # Deduplicate
    for item in fresh:
        if item["url"] not in _seen_urls and item["url"]:
            _seen_urls.add(item["url"])
            _news_cache.append(item)

    # Keep last 100 articles only
    _news_cache = _news_cache[-100:]
    _last_fetch = time.time()
    log.info("[NEWS] Cache updated: %d articles total", len(_news_cache))


def get_recent_news(n: int = 20) -> List[Dict]:
    return _news_cache[-n:]


async def news_loop() -> None:
    """Background loop: refresh news every SENTIMENT_INTERVAL seconds."""
    while True:
        await refresh_news()
        await asyncio.sleep(config.sentiment_interval)
