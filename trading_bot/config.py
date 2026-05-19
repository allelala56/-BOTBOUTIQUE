"""Central configuration — all params loaded from environment."""
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, default))


def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, default))


def _env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key, str(default)).lower()
    return v in ("1", "true", "yes")


@dataclass
class RiskConfig:
    max_position_pct: float = field(default_factory=lambda: _env_float("MAX_POSITION_PCT", 0.02))
    max_concurrent_positions: int = field(default_factory=lambda: _env_int("MAX_CONCURRENT_POSITIONS", 10))
    take_profit_pct: float = field(default_factory=lambda: _env_float("TAKE_PROFIT_PCT", 0.003))
    stop_loss_pct: float = field(default_factory=lambda: _env_float("STOP_LOSS_PCT", 0.0015))
    max_hold_seconds: int = field(default_factory=lambda: _env_int("MAX_HOLD_SECONDS", 90))
    max_daily_loss_pct: float = field(default_factory=lambda: _env_float("MAX_DAILY_LOSS_PCT", 0.03))
    max_drawdown_pct: float = field(default_factory=lambda: _env_float("MAX_DRAWDOWN_PCT", 0.10))
    max_spread_pct: float = field(default_factory=lambda: _env_float("MAX_SPREAD_PCT", 0.001))
    signal_threshold: float = field(default_factory=lambda: _env_float("SIGNAL_THRESHOLD", 0.60))
    consecutive_loss_cooldown: int = field(default_factory=lambda: _env_int("CONSECUTIVE_LOSS_COOLDOWN", 3))
    cooldown_seconds: int = field(default_factory=lambda: _env_int("COOLDOWN_SECONDS", 300))


@dataclass
class Config:
    # Capital
    initial_capital: float = field(default_factory=lambda: _env_float("INITIAL_CAPITAL", 10_000.0))
    paper_trading: bool = field(default_factory=lambda: _env_bool("PAPER_TRADING", True))

    # Exchange
    exchange_id: str = field(default_factory=lambda: os.getenv("EXCHANGE_ID", "binance"))
    binance_api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    binance_secret: str = field(default_factory=lambda: os.getenv("BINANCE_SECRET", ""))

    # Markets to trade
    symbols: List[str] = field(default_factory=lambda: [
        s.strip() for s in os.getenv(
            "SYMBOLS",
            "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,"
            "ADA/USDT,DOGE/USDT,AVAX/USDT,MATIC/USDT,DOT/USDT"
        ).split(",")
    ])

    # Analysis APIs
    alpha_vantage_key: str = field(default_factory=lambda: os.getenv("ALPHA_VANTAGE_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))

    # Telegram reporter
    telegram_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    # Simulation fees (applied in paper trading)
    slippage_pct: float = field(default_factory=lambda: _env_float("SLIPPAGE_PCT", 0.0005))
    fee_pct: float = field(default_factory=lambda: _env_float("FEE_PCT", 0.001))

    # Sentiment update interval (seconds)
    sentiment_interval: int = field(default_factory=lambda: _env_int("SENTIMENT_INTERVAL", 300))

    # Scan interval per symbol (seconds)
    scan_interval: float = field(default_factory=lambda: _env_float("SCAN_INTERVAL", 1.0))

    # Risk
    risk: RiskConfig = field(default_factory=RiskConfig)

    # Database
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "trades.db"))


# Singleton used across the app
config = Config()
