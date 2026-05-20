"""Flux de prix temps-réel via ccxt WebSocket (Binance) — pattern inspiré AI-Trader"""
import asyncio
import logging
import time
from collections import deque
from typing import Dict, List, Optional

import ccxt.pro as ccxtpro

from trading_bot.config import config

logger = logging.getLogger(__name__)

# Buffer OHLCV par symbole : 100 bougies 1m
OHLCV_BUFFERS: Dict[str, deque] = {s: deque(maxlen=100) for s in config.symbols}
LAST_PRICES: Dict[str, float] = {}
ORDERBOOKS: Dict[str, dict] = {}


async def _watch_ohlcv(exchange: ccxtpro.Exchange, symbol: str):
    """Stream OHLCV 1m pour un symbole avec retry exponentiel."""
    base_delay = 1.0
    while True:
        try:
            ohlcv = await exchange.watch_ohlcv(symbol, "1m")
            for candle in ohlcv:
                OHLCV_BUFFERS[symbol].append(candle)
            if ohlcv:
                LAST_PRICES[symbol] = ohlcv[-1][4]  # close
            base_delay = 1.0
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"[PRICE] {symbol} WS error: {e} — retry in {base_delay:.1f}s")
            await asyncio.sleep(base_delay)
            base_delay = min(base_delay * 2, 30.0)


async def _watch_orderbook(exchange: ccxtpro.Exchange, symbol: str):
    """Stream carnet d'ordres pour calcul du spread."""
    while True:
        try:
            ob = await exchange.watch_order_book(symbol, limit=5)
            ORDERBOOKS[symbol] = {
                "bid": ob["bids"][0][0] if ob["bids"] else 0,
                "ask": ob["asks"][0][0] if ob["asks"] else 0,
                "ts": time.time(),
            }
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(2)


def get_spread_pct(symbol: str) -> float:
    ob = ORDERBOOKS.get(symbol)
    if not ob or ob["bid"] == 0:
        return 999.0
    return (ob["ask"] - ob["bid"]) / ob["bid"]


def get_ohlcv(symbol: str) -> List:
    return list(OHLCV_BUFFERS[symbol])


def get_price(symbol: str) -> Optional[float]:
    return LAST_PRICES.get(symbol)


async def run_price_feeds():
    """Lance tous les flux WebSocket en parallèle."""
    exchange = ccxtpro.binance({
        "apiKey": config.binance_api_key or None,
        "secret": config.binance_secret or None,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    tasks = []
    for symbol in config.symbols:
        tasks.append(asyncio.create_task(_watch_ohlcv(exchange, symbol)))
        tasks.append(asyncio.create_task(_watch_orderbook(exchange, symbol)))
    try:
        await asyncio.gather(*tasks)
    finally:
        await exchange.close()
