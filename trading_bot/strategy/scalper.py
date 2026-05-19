"""
Machine à Cache — core scalping strategy.
Scans all symbols every SCAN_INTERVAL seconds, fires trades on valid signals.
"""
import asyncio
import logging
import time

from trading_bot.analysis.sentiment import analyze_sentiment
from trading_bot.analysis.signals import evaluate
from trading_bot.config import config
from trading_bot.execution.order_manager import OrderManager
from trading_bot.monitoring.database import TradeDB

log = logging.getLogger(__name__)


class Scalper:
    def __init__(self, order_manager: OrderManager, db: TradeDB):
        self.om = order_manager
        self.db = db
        self.running = False
        self.cycle = 0

    async def _update_sentiment(self) -> None:
        score, label = await analyze_sentiment()
        log.info("[SENTIMENT] score=%+.3f label=%s", score, label)

    async def _scan_symbol(self, symbol: str) -> None:
        try:
            signal = evaluate(symbol)
            if signal is None:
                return

            if signal.tradeable:
                log.debug(
                    "[SIGNAL] %s %s score=%.3f spread=%.4f%%",
                    symbol, signal.action, signal.score, signal.spread_pct * 100,
                )
                pos = self.om.submit(signal)
                if pos:
                    await self.db.save_open(pos)
        except Exception as exc:
            log.error("[SCAN] %s error: %s", symbol, exc)

    async def _scan_cycle(self) -> None:
        tasks = [self._scan_symbol(s) for s in config.symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.om.tick()

        # Persist newly closed trades
        for trade in self.om.trader.history[self.db.saved_count:]:
            await self.db.save_closed(trade)

    async def run(self) -> None:
        """Main loop: scan all markets every SCAN_INTERVAL seconds."""
        self.running = True
        log.info(
            "[SCALPER] Démarrage — %d marchés | capital=%.2f USDT | paper=%s",
            len(config.symbols), config.initial_capital, config.paper_trading,
        )

        # Initial sentiment fetch
        await self._update_sentiment()

        sentiment_timer = time.time()

        while self.running:
            loop_start = time.time()

            # Periodic sentiment refresh
            if time.time() - sentiment_timer >= config.sentiment_interval:
                asyncio.create_task(self._update_sentiment())
                sentiment_timer = time.time()

            await self._scan_cycle()
            self.cycle += 1

            # Sleep only remaining time (keeps cadence stable)
            elapsed = time.time() - loop_start
            sleep_for = max(0, config.scan_interval - elapsed)
            await asyncio.sleep(sleep_for)

    def stop(self) -> None:
        self.running = False
        log.info("[SCALPER] Arrêt demandé.")
