"""
Machine à Cache — Main entry point.
Orchestrates all async components: price streams, news, scalper, dashboard, Telegram.

Usage:
    python -m trading_bot.main
"""
import asyncio
import logging
import signal
import sys

from trading_bot.config import config
from trading_bot.data.news_fetcher import news_loop
from trading_bot.data.price_fetcher import start_streaming, stop_streaming
from trading_bot.execution.order_manager import OrderManager
from trading_bot.execution.paper_trader import PaperTrader
from trading_bot.monitoring.dashboard import Dashboard
from trading_bot.monitoring.database import TradeDB
from trading_bot.strategy.risk_manager import RiskManager
from trading_bot.strategy.scalper import Scalper
from trading_bot.telegram_reporter import reporter_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


async def main() -> None:
    log.info("=" * 60)
    log.info("  MACHINE À CACHE — Bot de Trading HF")
    log.info("  Capital initial : %.2f USDT", config.initial_capital)
    log.info("  Mode : %s", "PAPER TRADING" if config.paper_trading else "⚠️  LIVE MONEY")
    log.info("  Marchés : %s", ", ".join(config.symbols))
    log.info("=" * 60)

    # --- Build components ---
    db = TradeDB()
    await db.init()

    risk    = RiskManager()
    trader  = PaperTrader(risk)
    orders  = OrderManager(trader, risk)
    scalper = Scalper(orders, db)
    dash    = Dashboard(trader, risk)

    # Graceful shutdown
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _shutdown(sig, frame):
        log.info("Signal %s reçu — arrêt en cours...", sig)
        scalper.stop()
        shutdown_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # --- Launch all coroutines ---
    tasks = [
        asyncio.create_task(start_streaming(),     name="price_streams"),
        asyncio.create_task(news_loop(),           name="news_loop"),
        asyncio.create_task(scalper.run(),         name="scalper"),
        asyncio.create_task(dash.run(),            name="dashboard"),
        asyncio.create_task(reporter_loop(trader), name="telegram_reporter"),
        asyncio.create_task(shutdown_event.wait(), name="shutdown_watcher"),
    ]

    log.info("Tous les composants démarrés.")
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # Teardown
    for task in pending:
        task.cancel()
    await stop_streaming()

    stats = trader.stats()
    log.info("Session terminée — P&L final : %+.4f USDT | Trades : %d",
             stats["total_pnl"], stats["total_trades"])


if __name__ == "__main__":
    asyncio.run(main())
