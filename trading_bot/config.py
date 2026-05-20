"""Configuration centrale — Machine à Cache Trading Bot"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


def _str(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass
class Config:
    # Capital & mode
    initial_capital: float = field(default_factory=lambda: _float("INITIAL_CAPITAL", 10000.0))
    paper_trading: bool = field(default_factory=lambda: _bool("PAPER_TRADING", True))
    trading_mode: str = field(default_factory=lambda: _str("TRADING_MODE", "scalper"))

    # Exchange
    binance_api_key: str = field(default_factory=lambda: _str("BINANCE_API_KEY"))
    binance_secret: str = field(default_factory=lambda: _str("BINANCE_SECRET"))

    # Marchés à trader simultanément
    symbols: list = field(default_factory=lambda: [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
        "XRP/USDT", "ADA/USDT", "AVAX/USDT", "DOGE/USDT",
        "MATIC/USDT", "DOT/USDT", "LINK/USDT", "LTC/USDT",
    ])

    # APIs analyse
    alpha_vantage_key: str = field(default_factory=lambda: _str("ALPHA_VANTAGE_KEY"))
    anthropic_api_key: str = field(default_factory=lambda: _str("ANTHROPIC_API_KEY"))

    # Gestion du risque
    max_position_pct: float = field(default_factory=lambda: _float("MAX_POSITION_PCT", 0.02))
    max_daily_loss_pct: float = field(default_factory=lambda: _float("MAX_DAILY_LOSS_PCT", 0.03))
    max_drawdown_pct: float = field(default_factory=lambda: _float("MAX_DRAWDOWN_PCT", 0.10))
    max_concurrent_positions: int = field(default_factory=lambda: _int("MAX_CONCURRENT_POSITIONS", 10))
    take_profit_pct: float = field(default_factory=lambda: _float("TAKE_PROFIT_PCT", 0.003))
    stop_loss_pct: float = field(default_factory=lambda: _float("STOP_LOSS_PCT", 0.0015))
    max_hold_seconds: int = field(default_factory=lambda: _int("MAX_HOLD_SECONDS", 90))
    max_spread_pct: float = field(default_factory=lambda: _float("MAX_SPREAD_PCT", 0.001))
    consecutive_loss_cooldown: int = field(default_factory=lambda: _int("CONSECUTIVE_LOSS_COOLDOWN", 300))
    max_consecutive_losses: int = field(default_factory=lambda: _int("MAX_CONSECUTIVE_LOSSES", 3))

    # Signal
    signal_threshold: float = field(default_factory=lambda: _float("SIGNAL_THRESHOLD", 0.6))
    sentiment_weight: float = field(default_factory=lambda: _float("SENTIMENT_WEIGHT", 0.3))
    technical_weight: float = field(default_factory=lambda: _float("TECHNICAL_WEIGHT", 0.7))

    # Paper trading simulation
    slippage_pct: float = field(default_factory=lambda: _float("SLIPPAGE_PCT", 0.0005))
    fee_pct: float = field(default_factory=lambda: _float("FEE_PCT", 0.001))

    # News
    news_refresh_seconds: int = field(default_factory=lambda: _int("NEWS_REFRESH_SECONDS", 300))

    # Telegram
    bot_token: str = field(default_factory=lambda: _str("BOT_TOKEN"))
    telegram_chat_id: str = field(default_factory=lambda: _str("TELEGRAM_CHAT_ID"))

    # DB
    db_path: str = field(default_factory=lambda: _str("DB_PATH", "trades.db"))

    # Scan interval
    scan_interval: float = field(default_factory=lambda: _float("SCAN_INTERVAL", 1.0))


config = Config()
