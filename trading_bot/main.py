"""Machine à Cache — Point d'entrée principal"""
import asyncio
import logging
import signal
import sys
import time
from datetime import datetime

from trading_bot.config import config
from trading_bot.monitoring.database import db
from trading_bot.data.news_fetcher import news_refresh_loop, refresh_news
from trading_bot.data.price_fetcher import run_price_feeds
from trading_bot.analysis.sentiment import sentiment_loop, refresh_sentiment
from trading_bot.strategy.scalper import scalper_loop
from trading_bot.monitoring.dashboard import dashboard_loop
from trading_bot.telegram_reporter import reporter_loop, send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


async def startup():
    """Initialisation avant le démarrage des boucles."""
    logger.info("=" * 60)
    logger.info("  MACHINE À CACHE — Trading Bot v1.0")
    logger.info(f"  Mode: {'PAPER TRADING' if config.paper_trading else '⚠️  LIVE TRADING'}")
    logger.info(f"  Capital: {config.initial_capital:,.2f} USDT")
    logger.info(f"  Marchés: {len(config.symbols)} paires")
    logger.info(f"  TP: {config.take_profit_pct:.1%} | SL: {config.stop_loss_pct:.1%}")
    logger.info(f"  Max positions: {config.max_concurrent_positions}")
    logger.info("=" * 60)

    # DB
    await db.connect()
    logger.info("[INIT] Base de données connectée")

    # Première charge de news et sentiment (en parallèle)
    logger.info("[INIT] Chargement des news et sentiment initial...")
    await asyncio.gather(
        refresh_news(),
        refresh_sentiment(),
        return_exceptions=True,
    )
    logger.info("[INIT] Données initiales chargées")

    if config.bot_token and config.telegram_chat_id:
        await send_message(
            f"🚀 <b>Machine à Cache démarrée</b>\n"
            f"Capital: {config.initial_capital:,.0f}$ | "
            f"{'PAPER' if config.paper_trading else 'LIVE'}"
        )


async def main():
    await startup()

    # Lancement de toutes les coroutines en parallèle
    tasks = [
        asyncio.create_task(run_price_feeds(),     name="price-feeds"),
        asyncio.create_task(news_refresh_loop(),   name="news-loop"),
        asyncio.create_task(sentiment_loop(),      name="sentiment-loop"),
        asyncio.create_task(scalper_loop(),        name="scalper"),
        asyncio.create_task(dashboard_loop(),      name="dashboard"),
        asyncio.create_task(reporter_loop(),       name="telegram-reporter"),
    ]

    def _shutdown(sig_name):
        logger.warning(f"[MAIN] Signal {sig_name} reçu — arrêt graceful")
        for t in tasks:
            t.cancel()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: _shutdown(s.name))

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    finally:
        await db.close()
        logger.info("[MAIN] Bot arrêté proprement.")


if __name__ == "__main__":
    asyncio.run(main())
