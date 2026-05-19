"""
Telegram reporter: sends periodic P&L summaries and trade alerts.
Non-blocking; only active if BOT_TOKEN and TELEGRAM_CHAT_ID are set.
"""
import asyncio
import logging
import time

import telebot

from trading_bot.config import config
from trading_bot.analysis.sentiment import get_cached_sentiment

log = logging.getLogger(__name__)

_bot = None
_last_report = 0.0
REPORT_INTERVAL = 3600  # send summary every hour


def _get_bot():
    global _bot
    if _bot is None and config.telegram_token:
        _bot = telebot.TeleBot(config.telegram_token, threaded=False)
    return _bot


def _send(msg: str) -> None:
    if not config.telegram_chat_id or not config.telegram_token:
        return
    bot = _get_bot()
    if bot is None:
        return
    try:
        bot.send_message(config.telegram_chat_id, msg, parse_mode="Markdown")
    except Exception as exc:
        log.warning("[TELEGRAM] Send failed: %s", exc)


def send_trade_alert(side: str, symbol: str, price: float, size_quote: float) -> None:
    emoji = "🟢" if side == "BUY" else "🔴"
    msg = (
        f"{emoji} *TRADE OUVERT*\n"
        f"`{side}` {symbol}\n"
        f"Prix : `{price:.6f}` USDT\n"
        f"Taille : `{size_quote:.2f}` USDT"
    )
    _send(msg)


def send_trade_close(symbol: str, pnl: float, pnl_pct: float, reason: str) -> None:
    emoji = "✅" if pnl > 0 else "❌"
    msg = (
        f"{emoji} *TRADE FERMÉ* — {symbol}\n"
        f"P&L : `{pnl:+.4f}` USDT (`{pnl_pct * 100:+.2f}%`)\n"
        f"Raison : `{reason}`"
    )
    _send(msg)


def send_hourly_report(stats: dict) -> None:
    global _last_report
    now = time.time()
    if now - _last_report < REPORT_INTERVAL:
        return
    _last_report = now

    sentiment_score, sentiment_label = get_cached_sentiment()
    initial = config.initial_capital
    capital = stats.get("capital", initial)
    total_return = (capital - initial) / initial * 100

    msg = (
        f"📊 *RAPPORT MACHINE À CACHE*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 Capital : `{capital:,.2f}` USDT\n"
        f"📈 Rendement : `{total_return:+.2f}%`\n"
        f"💵 P&L total : `{stats.get('total_pnl', 0.0):+.4f}` USDT\n"
        f"📉 Drawdown : `{stats.get('drawdown', 0.0):.2%}`\n"
        f"🎯 Win rate : `{stats.get('win_rate', 0.0):.1%}`\n"
        f"📊 Trades : `{stats.get('total_trades', 0)}`\n"
        f"🧠 Sentiment : `{sentiment_label}` ({sentiment_score:+.2f})\n"
        f"📍 Positions : `{stats.get('open_positions', 0)}`"
    )
    _send(msg)


async def reporter_loop(paper_trader) -> None:
    """Background loop: send hourly reports."""
    while True:
        await asyncio.sleep(60)
        send_hourly_report(paper_trader.stats())
