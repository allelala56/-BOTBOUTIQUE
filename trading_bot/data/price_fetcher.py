"""
Real-time OHLCV price fetcher via Binance WebSocket (ccxt.pro).
Maintains a rolling buffer of candles per symbol.
Inspired by HKUDS/AI-Trader price_fetcher.py — retry + backoff pattern.
"""
import asyncio
import logging
import random
import time
from collections import deque
from typing import Dict, List, Optional

import ccxt.pro as ccxtpro
import pandas as pd

from trading_bot.config import config

log = logging.getLogger(__name__)

# Candles per symbol (1-minute OHLCV)
CANDLE_BUFFER = 200

# {symbol: deque of OHLCV rows}
_candles: Dict[str, deque] = {s: deque(maxlen=CANDLE_BUFFER) for s in config.symbols}
# {symbol: {"bid": float, "ask": float, "spread_pct": float}}
_orderbook: Dict[str, dict] = {}

_exchange: Optional[ccxtpro.Exchange] = None
_running = False


def _build_exchange() -> ccxtpro.Exchange:
    ex_class = getattr(ccxtpro, config.exchange_id)
    params: dict = {"enableRateLimit": True}
    if config.binance_api_key:
        params["apiKey"] = config.binance_api_key
        params["secret"] = config.binance_secret
    return ex_class(params)


async def _watch_ohlcv(symbol: str) -> None:
    """Continuously stream 1-minute candles for one symbol."""
    global _exchange
    backoff = 1.0
    while _running:
        try:
            candles = await _exchange.watch_ohlcv(symbol, "1m")
            for c in candles:
                _candles[symbol].append(c)
            backoff = 1.0
        except ccxtpro.NetworkError as exc:
            log.warning("[%s] NetworkError: %s — retry in %.1fs", symbol, exc, backoff)
            await asyncio.sleep(backoff + random.uniform(0, backoff * 0.25))
            backoff = min(backoff * 2, 60.0)
        except Exception as exc:
            log.error("[%s] Unexpected error: %s", symbol, exc)
            await asyncio.sleep(5)


async def _watch_orderbook(symbol: str) -> None:
    """Stream best bid/ask for spread monitoring."""
    global _exchange
    backoff = 1.0
    while _running:
        try:
            ob = await _exchange.watch_order_book(symbol, 1)
            bid = ob["bids"][0][0] if ob["bids"] else 0
            ask = ob["asks"][0][0] if ob["asks"] else 0
            spread_pct = (ask - bid) / ask if ask else 0
            _orderbook[symbol] = {"bid": bid, "ask": ask, "spread_pct": spread_pct}
            backoff = 1.0
        except ccxtpro.NetworkError as exc:
            log.warning("[%s] OB NetworkError: %s — retry in %.1fs", symbol, exc, backoff)
            await asyncio.sleep(backoff + random.uniform(0, backoff * 0.25))
            backoff = min(backoff * 2, 60.0)
        except Exception as exc:
            log.error("[%s] OB error: %s", symbol, exc)
            await asyncio.sleep(5)


async def start_streaming() -> None:
    """Launch all WebSocket streams. Call once at startup."""
    global _exchange, _running
    _exchange = _build_exchange()
    _running = True
    tasks = []
    for symbol in config.symbols:
        tasks.append(asyncio.create_task(_watch_ohlcv(symbol), name=f"ohlcv_{symbol}"))
        tasks.append(asyncio.create_task(_watch_orderbook(symbol), name=f"ob_{symbol}"))
    log.info("Price streams started for %d symbols", len(config.symbols))
    await asyncio.gather(*tasks, return_exceptions=True)


async def stop_streaming() -> None:
    global _running, _exchange
    _running = False
    if _exchange:
        await _exchange.close()


def get_candles(symbol: str) -> Optional[pd.DataFrame]:
    """Return OHLCV DataFrame for a symbol (newest row last)."""
    buf = list(_candles.get(symbol, []))
    if len(buf) < 30:
        return None
    df = pd.DataFrame(buf, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)


def get_orderbook(symbol: str) -> dict:
    return _orderbook.get(symbol, {"bid": 0.0, "ask": 0.0, "spread_pct": 1.0})


def get_latest_price(symbol: str) -> float:
    ob = get_orderbook(symbol)
    if ob["bid"] and ob["ask"]:
        return (ob["bid"] + ob["ask"]) / 2
    buf = list(_candles.get(symbol, []))
    return buf[-1][4] if buf else 0.0  # close price
