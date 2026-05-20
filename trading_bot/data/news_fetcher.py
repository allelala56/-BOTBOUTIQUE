"""Récupération news crypto — RSS (xml stdlib) + Alpha Vantage"""
import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Dict
from urllib.parse import urlencode

import aiohttp

from trading_bot.config import config

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("CoinDesk",      "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt",       "https://decrypt.co/feed"),
    ("BeInCrypto",    "https://beincrypto.com/feed/"),
]

_news_cache: List[Dict] = []
_cache_ts: float = 0.0


def _parse_rss(xml_text: str, source: str) -> List[Dict]:
    """Parse un feed RSS avec xml.etree.ElementTree."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        # RSS 2.0
        for item in root.findall(".//item")[:15]:
            title = item.findtext("title", "")
            link  = item.findtext("link", "")
            desc  = item.findtext("description", "")[:300]
            pub   = item.findtext("pubDate", "")
            if title:
                articles.append({"title": title, "url": link,
                                  "source": source, "published": pub,
                                  "summary": desc})
        # Atom
        if not articles:
            for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry")[:15]:
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                link  = link_el.get("href", "") if link_el is not None else ""
                summ  = entry.findtext("{http://www.w3.org/2005/Atom}summary", "")[:300]
                pub   = entry.findtext("{http://www.w3.org/2005/Atom}updated", "")
                if title:
                    articles.append({"title": title, "url": link,
                                      "source": source, "published": pub,
                                      "summary": summ})
    except ET.ParseError as e:
        logger.debug(f"[NEWS] XML parse error ({source}): {e}")
    return articles


async def _fetch_rss(session: aiohttp.ClientSession, name: str, url: str) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TradingBot/1.0)"}
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=12),
                               headers=headers) as r:
            text = await r.text()
        return _parse_rss(text, name)
    except Exception as e:
        logger.debug(f"[NEWS] RSS {name}: {e}")
        return []


async def _fetch_alpha_vantage(session: aiohttp.ClientSession) -> List[Dict]:
    if not config.alpha_vantage_key:
        return []
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers":  "CRYPTO:BTC,CRYPTO:ETH",
        "limit":    "20",
        "apikey":   config.alpha_vantage_key,
    }
    url = "https://www.alphavantage.co/query?" + urlencode(params)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
            data = await r.json()
        return [
            {
                "title":           item.get("title", ""),
                "url":             item.get("url", ""),
                "source":          item.get("source", "AlphaVantage"),
                "published":       item.get("time_published", ""),
                "summary":         item.get("summary", "")[:300],
                "sentiment_score": float(item.get("overall_sentiment_score", 0)),
                "sentiment_label": item.get("overall_sentiment_label", "Neutral"),
            }
            for item in data.get("feed", [])
        ]
    except Exception as e:
        logger.debug(f"[NEWS] AlphaVantage: {e}")
        return []


def _deduplicate(articles: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for a in articles:
        key = a.get("url") or f"{a['title']}{a['source']}"
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


async def refresh_news():
    global _news_cache, _cache_ts
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [_fetch_rss(session, n, u) for n, u in RSS_FEEDS]
        tasks.append(_fetch_alpha_vantage(session))
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = []
    for r in results:
        if isinstance(r, list):
            all_articles.extend(r)

    _news_cache = _deduplicate(all_articles)[:50]
    _cache_ts = time.time()
    logger.info(f"[NEWS] {len(_news_cache)} articles chargés")


def get_news(max_items: int = 20) -> List[Dict]:
    return _news_cache[:max_items]


async def news_refresh_loop():
    while True:
        try:
            await refresh_news()
        except Exception as e:
            logger.error(f"[NEWS] Refresh error: {e}")
        await asyncio.sleep(config.news_refresh_seconds)
