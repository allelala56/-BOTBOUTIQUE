"""Indicateurs techniques — RSI, MACD, Bollinger Bands, EMA"""
import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class TechnicalSignal:
    symbol: str
    direction: int       # +1 = BUY, -1 = SELL, 0 = NEUTRAL
    score: float         # 0.0 à 1.0
    rsi: float
    macd: float
    macd_signal: float
    bb_position: float   # -1 (bas bande) à +1 (haut bande)
    price: float
    volume_ratio: float  # volume actuel / volume moyen


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series):
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd_line = ema12 - ema26
    signal_line = _ema(macd_line, 9)
    return macd_line.iloc[-1], signal_line.iloc[-1]


def _bollinger(close: pd.Series, period: int = 20) -> tuple:
    ma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = (ma + 2 * std).iloc[-1]
    lower = (ma - 2 * std).iloc[-1]
    mid = ma.iloc[-1]
    price = close.iloc[-1]
    # position normalisée entre -1 (sur bande basse) et +1 (sur bande haute)
    band_range = upper - lower
    if band_range == 0:
        return 0.0, upper, lower
    position = 2 * (price - lower) / band_range - 1
    return float(np.clip(position, -1.5, 1.5)), upper, lower


def compute_signal(symbol: str, ohlcv: List) -> Optional[TechnicalSignal]:
    """Calcule les indicateurs TA et génère un signal directionnel."""
    if len(ohlcv) < 30:
        return None
    try:
        df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        rsi = _rsi(close)
        macd, macd_sig = _macd(close)
        bb_pos, bb_upper, bb_lower = _bollinger(close)
        price = close.iloc[-1]
        vol_ratio = volume.iloc[-1] / volume.iloc[-10:].mean() if volume.iloc[-10:].mean() > 0 else 1.0

        direction = 0
        score = 0.0

        # --- Signal BUY ---
        buy_points = 0.0
        if rsi < 30:
            buy_points += 0.4
        elif rsi < 40:
            buy_points += 0.2
        if macd > macd_sig and macd > 0:
            buy_points += 0.3
        elif macd > macd_sig:
            buy_points += 0.15
        if bb_pos < -0.7:
            buy_points += 0.3
        if vol_ratio > 1.5:
            buy_points += 0.1

        # --- Signal SELL ---
        sell_points = 0.0
        if rsi > 70:
            sell_points += 0.4
        elif rsi > 60:
            sell_points += 0.2
        if macd < macd_sig and macd < 0:
            sell_points += 0.3
        elif macd < macd_sig:
            sell_points += 0.15
        if bb_pos > 0.7:
            sell_points += 0.3
        if vol_ratio > 1.5:
            sell_points += 0.1

        if buy_points > sell_points:
            direction = 1
            score = min(buy_points, 1.0)
        elif sell_points > buy_points:
            direction = -1
            score = min(sell_points, 1.0)

        return TechnicalSignal(
            symbol=symbol, direction=direction, score=score,
            rsi=rsi, macd=macd, macd_signal=macd_sig,
            bb_position=bb_pos, price=price, volume_ratio=float(vol_ratio)
        )
    except Exception as e:
        logger.debug(f"[TA] {symbol} error: {e}")
        return None
