"""
Signal aggregator: combines technical score + sentiment bias into a final trade signal.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from trading_bot.analysis.technical import TechnicalSignal, compute_signal
from trading_bot.analysis.sentiment import get_cached_sentiment
from trading_bot.config import config
from trading_bot.data.price_fetcher import get_candles, get_orderbook

log = logging.getLogger(__name__)

TECH_WEIGHT = 0.70
SENT_WEIGHT = 0.30


@dataclass
class TradeSignal:
    symbol: str
    action: str          # "BUY" | "SELL" | "HOLD"
    score: float         # final composite score
    price: float
    spread_pct: float
    technical: TechnicalSignal
    sentiment_score: float
    tradeable: bool      # passes all filters


def evaluate(symbol: str) -> Optional[TradeSignal]:
    """
    Evaluate a symbol and return a TradeSignal or None if data is unavailable.
    """
    df = get_candles(symbol)
    if df is None or df.empty:
        return None

    tech = compute_signal(df)
    if tech is None:
        return None

    sentiment_score, _ = get_cached_sentiment()

    # Combine scores: technical dominates, sentiment acts as bias
    composite = TECH_WEIGHT * tech.score + SENT_WEIGHT * sentiment_score
    composite = max(-1.0, min(1.0, composite))

    ob = get_orderbook(symbol)
    spread_pct = ob.get("spread_pct", 1.0)
    price = ob.get("ask", 0.0) if composite > 0 else ob.get("bid", 0.0)
    if price == 0.0:
        price = float(df["close"].iloc[-1])

    threshold = config.risk.signal_threshold
    max_spread = config.risk.max_spread_pct

    tradeable = (
        abs(composite) >= threshold
        and spread_pct <= max_spread
        and price > 0
    )

    if composite > threshold:
        action = "BUY"
    elif composite < -threshold:
        action = "SELL"
    else:
        action = "HOLD"

    return TradeSignal(
        symbol=symbol,
        action=action,
        score=composite,
        price=price,
        spread_pct=spread_pct,
        technical=tech,
        sentiment_score=sentiment_score,
        tradeable=tradeable and action != "HOLD",
    )
