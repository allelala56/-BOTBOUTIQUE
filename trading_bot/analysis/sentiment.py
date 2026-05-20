"""Analyse de sentiment des news via Claude Haiku"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass

import anthropic

from trading_bot.config import config
from trading_bot.data.news_fetcher import get_news

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    score: float       # -1.0 (très baissier) à +1.0 (très haussier)
    label: str
    summary: str
    ts: float


_cache: SentimentResult = SentimentResult(score=0.0, label="neutral", summary="Aucune analyse", ts=0.0)
_CACHE_TTL = 300.0   # 5 minutes
_lock = asyncio.Lock()


_PROMPT = """Tu es un analyste crypto expert. Voici {n} titres d'articles de news récents sur les crypto-monnaies.

NEWS:
{news}

Analyse l'impact global sur le marché crypto et réponds UNIQUEMENT en JSON valide:
{{
  "score": <float entre -1.0 et 1.0>,
  "label": "<très_baissier | baissier | neutre | haussier | très_haussier>",
  "summary": "<résumé en 1 phrase max>"
}}

score = -1.0 signifie très baissier (crash, hack, ban), +1.0 signifie très haussier (ETF, adoption, ATH)."""


async def refresh_sentiment() -> SentimentResult:
    global _cache
    if not config.anthropic_api_key:
        return _cache

    async with _lock:
        if time.time() - _cache.ts < _CACHE_TTL:
            return _cache

    news = get_news(20)
    if not news:
        return _cache

    news_text = "\n".join(f"- {a['title']}" for a in news[:20])
    prompt = _PROMPT.format(n=len(news[:20]), news=news_text)

    try:
        client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        data = json.loads(raw)
        result = SentimentResult(
            score=float(max(-1.0, min(1.0, data.get("score", 0.0)))),
            label=data.get("label", "neutre"),
            summary=data.get("summary", ""),
            ts=time.time(),
        )
        async with _lock:
            _cache = result
        logger.info(f"[SENTIMENT] score={result.score:.2f} ({result.label}) — {result.summary}")
        return result
    except Exception as e:
        logger.warning(f"[SENTIMENT] Erreur Claude: {e}")
        return _cache


def get_sentiment() -> SentimentResult:
    return _cache


async def sentiment_loop():
    """Met à jour le sentiment toutes les 5 minutes."""
    while True:
        try:
            await refresh_sentiment()
        except Exception as e:
            logger.error(f"[SENTIMENT] Loop error: {e}")
        await asyncio.sleep(_CACHE_TTL)
