"""
Order manager: bridges the scalper strategy with the paper (or live) trader.
Prevents duplicate positions on the same symbol.
"""
import logging
from typing import Optional, Set

from trading_bot.analysis.signals import TradeSignal
from trading_bot.execution.paper_trader import PaperTrader, Position
from trading_bot.strategy.risk_manager import RiskManager

log = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, paper_trader: PaperTrader, risk_manager: RiskManager):
        self.trader = paper_trader
        self.risk = risk_manager
        self._active_symbols: Set[str] = set()

    def submit(self, signal: TradeSignal) -> Optional[Position]:
        if not signal.tradeable:
            return None

        if signal.symbol in self._active_symbols:
            return None  # already have a position on this symbol

        allowed, reason = self.risk.can_trade()
        if not allowed:
            log.debug("[ORDER] Blocked — %s", reason)
            return None

        size_quote = self.risk.position_size(signal.price)
        if size_quote <= 0:
            return None

        pos = self.trader.open_position(
            symbol=signal.symbol,
            side=signal.action,
            price=signal.price,
            size_quote=size_quote,
            signal_score=signal.score,
        )
        if pos:
            self._active_symbols.add(signal.symbol)
        return pos

    async def tick(self) -> None:
        """Must be called each scan cycle to process TP/SL/TIME exits."""
        await self.trader.tick()
        # Sync active symbols with open positions
        open_symbols = {pos.symbol for pos in self.trader.positions.values()}
        self._active_symbols = open_symbols
