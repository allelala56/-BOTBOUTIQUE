"""Rapports Telegram — P&L et alertes (optionnel)"""
import asyncio
import logging
import time
from typing import Optional

import aiohttp

from trading_bot.config import config
from trading_bot.strategy.risk_manager import risk_manager
from trading_bot.monitoring.database import db

logger = logging.getLogger(__name__)

_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def send_message(text: str):
    """Envoie un message Telegram si configuré."""
    if not config.bot_token or not config.telegram_chat_id:
        return
    url = _API_URL.format(token=config.bot_token)
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    logger.warning(f"[TG] Status {r.status}")
    except Exception as e:
        logger.debug(f"[TG] Error: {e}")


async def send_daily_report():
    """Rapport de fin de journée."""
    stats = await db.get_today_stats()
    risk = risk_manager.get_stats()
    win_rate = stats["wins"] / stats["trades"] * 100 if stats["trades"] > 0 else 0

    emoji = "🟢" if stats["net_pnl"] >= 0 else "🔴"
    text = (
        f"{emoji} <b>Machine à Cache — Rapport Journalier</b>\n\n"
        f"📊 Trades: {stats['trades']} ({stats['wins']}W / {stats['losses']}L)\n"
        f"🎯 Win Rate: {win_rate:.1f}%\n"
        f"💰 P&amp;L net: {stats['net_pnl']:+.2f}$\n"
        f"💸 Frais: {stats['total_fees']:.2f}$\n"
        f"🏦 Capital: {risk['capital']:.2f}$\n"
        f"📉 Drawdown: {risk['drawdown']:.2%}"
    )
    await send_message(text)


async def send_alert(message: str):
    """Alerte urgente."""
    await send_message(f"⚠️ <b>ALERTE</b>: {message}")


async def reporter_loop():
    """Envoie un rapport toutes les heures."""
    while True:
        await asyncio.sleep(3600)
        try:
            await send_daily_report()
        except Exception as e:
            logger.error(f"[TG] Reporter error: {e}")
