"""Génération et scoring final des signaux de trading."""
import logging
from dataclasses import dataclass
from typing import Optional

from trading_bot.config import config
from trading_bot.analysis.technical import TechnicalSignal
from trading_bot.analysis.sentiment import get_sentiment

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    symbol: str
    direction: int       # +1 BUY / -1 SELL
    final_score: float   # 0.0 à 1.0
    tech_score: float
    sentiment_score: float
    price: float
    rsi: float


def compute_final_signal(tech: TechnicalSignal) -> Optional[TradeSignal]:
    """Combine signal technique + sentiment en un score final."""
    if tech.direction == 0 or tech.score < 0.3:
        return None

    sentiment = get_sentiment()
    # Sentiment score normalisé : -1..+1 → 0..1 dans le sens du trade
    raw_sent = sentiment.score * tech.direction  # positif si sentiment aligne direction
    sentiment_score = (raw_sent + 1.0) / 2.0    # normalisation 0..1

    final = (config.technical_weight * tech.score +
             config.sentiment_weight * sentiment_score)

    if final < config.signal_threshold:
        return None

    logger.debug(
        f"[SIGNAL] {tech.symbol} {'BUY' if tech.direction > 0 else 'SELL'} "
        f"score={final:.3f} (tech={tech.score:.2f} sent={sentiment_score:.2f})"
    )
    return TradeSignal(
        symbol=tech.symbol,
        direction=tech.direction,
        final_score=final,
        tech_score=tech.score,
        sentiment_score=sentiment_score,
        price=tech.price,
        rsi=tech.rsi,
    )
