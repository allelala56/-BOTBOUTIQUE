"""
Technical analysis: RSI, MACD, Bollinger Bands, EMA via pandas-ta.
Returns a normalized signal score between -1 and +1.
"""
import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import pandas_ta as ta

log = logging.getLogger(__name__)


@dataclass
class TechnicalSignal:
    score: float          # -1 (strong sell) to +1 (strong buy)
    direction: str        # "BUY" | "SELL" | "NEUTRAL"
    rsi: float
    macd_hist: float
    bb_position: float    # 0=lower band, 0.5=middle, 1=upper band
    ema_trend: str        # "UP" | "DOWN" | "FLAT"
    confidence: float     # 0 to 1


def compute_signal(df: pd.DataFrame) -> Optional[TechnicalSignal]:
    """
    Compute a composite technical signal from OHLCV data.
    Requires at least 30 rows.
    """
    if df is None or len(df) < 30:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # --- RSI ---
    rsi_s = ta.rsi(close, length=14)
    rsi = float(rsi_s.iloc[-1]) if rsi_s is not None and not rsi_s.empty else 50.0

    # --- MACD ---
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        hist_col = [c for c in macd_df.columns if "MACDh" in c]
        macd_hist = float(macd_df[hist_col[0]].iloc[-1]) if hist_col else 0.0
        macd_prev = float(macd_df[hist_col[0]].iloc[-2]) if hist_col and len(macd_df) > 1 else 0.0
    else:
        macd_hist = macd_prev = 0.0

    # --- Bollinger Bands ---
    bb = ta.bbands(close, length=20, std=2.0)
    if bb is not None and not bb.empty:
        lower_col = [c for c in bb.columns if "BBL" in c]
        upper_col = [c for c in bb.columns if "BBU" in c]
        mid_col   = [c for c in bb.columns if "BBM" in c]
        if lower_col and upper_col:
            bb_lower = float(bb[lower_col[0]].iloc[-1])
            bb_upper = float(bb[upper_col[0]].iloc[-1])
            current = float(close.iloc[-1])
            band_range = bb_upper - bb_lower if bb_upper != bb_lower else 1
            bb_position = (current - bb_lower) / band_range
        else:
            bb_position = 0.5
    else:
        bb_position = 0.5

    # --- EMA trend (fast vs slow) ---
    ema_fast = ta.ema(close, length=9)
    ema_slow = ta.ema(close, length=21)
    if ema_fast is not None and ema_slow is not None and not ema_fast.empty:
        ef = float(ema_fast.iloc[-1])
        es = float(ema_slow.iloc[-1])
        if ef > es * 1.0005:
            ema_trend = "UP"
        elif ef < es * 0.9995:
            ema_trend = "DOWN"
        else:
            ema_trend = "FLAT"
    else:
        ema_trend = "FLAT"

    # --- Volume surge ---
    vol_mean = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else float(volume.mean())
    vol_surge = float(volume.iloc[-1]) > vol_mean * 1.5

    # --- Scoring ---
    score = 0.0
    signals_count = 0

    # RSI component (oversold→buy, overbought→sell)
    if rsi < 30:
        score += 0.35
    elif rsi < 40:
        score += 0.15
    elif rsi > 70:
        score -= 0.35
    elif rsi > 60:
        score -= 0.15
    signals_count += 1

    # MACD histogram direction + crossover
    if macd_hist > 0 and macd_prev <= 0:  # fresh bullish cross
        score += 0.35
    elif macd_hist > 0:
        score += 0.15
    elif macd_hist < 0 and macd_prev >= 0:  # fresh bearish cross
        score -= 0.35
    elif macd_hist < 0:
        score -= 0.15
    signals_count += 1

    # Bollinger Band position
    if bb_position < 0.1:    # near lower band → potential bounce
        score += 0.2
    elif bb_position > 0.9:  # near upper band → potential reversal
        score -= 0.2
    signals_count += 1

    # EMA trend alignment
    if ema_trend == "UP":
        score += 0.1
    elif ema_trend == "DOWN":
        score -= 0.1
    signals_count += 1

    # Volume surge adds confidence to direction
    if vol_surge:
        score *= 1.2  # amplify signal on high volume

    # Clamp to [-1, 1]
    score = max(-1.0, min(1.0, score))

    # Confidence = how many indicators agree
    if abs(score) > 0.7:
        confidence = 0.9
    elif abs(score) > 0.4:
        confidence = 0.7
    elif abs(score) > 0.2:
        confidence = 0.5
    else:
        confidence = 0.3

    if score > 0.1:
        direction = "BUY"
    elif score < -0.1:
        direction = "SELL"
    else:
        direction = "NEUTRAL"

    return TechnicalSignal(
        score=score,
        direction=direction,
        rsi=rsi,
        macd_hist=macd_hist,
        bb_position=bb_position,
        ema_trend=ema_trend,
        confidence=confidence,
    )
