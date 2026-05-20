"""Cycle de vie des ordres — ouverture, suivi, fermeture"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from trading_bot.config import config

logger = logging.getLogger(__name__)


@dataclass
class Position:
    id: str
    symbol: str
    side: str              # "BUY" ou "SELL"
    entry_price: float
    quantity: float        # en USDT investi
    tp_price: float
    sl_price: float
    opened_at: float
    signal_score: float
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0

    def update_price(self, price: float):
        self.current_price = price
        if self.side == "BUY":
            self.pnl_pct = (price - self.entry_price) / self.entry_price
        else:
            self.pnl_pct = (self.entry_price - price) / self.entry_price
        self.pnl = self.quantity * self.pnl_pct

    def should_close(self) -> Optional[str]:
        if self.side == "BUY":
            if self.current_price >= self.tp_price:
                return "TP"
            if self.current_price <= self.sl_price:
                return "SL"
        else:
            if self.current_price <= self.tp_price:
                return "TP"
            if self.current_price >= self.sl_price:
                return "SL"
        if time.time() - self.opened_at >= config.max_hold_seconds:
            return "TIMEOUT"
        return None

    @property
    def hold_seconds(self) -> float:
        return time.time() - self.opened_at


class OrderManager:
    def __init__(self):
        self._positions: Dict[str, Position] = {}
        self._lock = asyncio.Lock()
        self._id_counter = 0

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"POS-{self._id_counter:05d}"

    async def open_position(self, symbol: str, side: str, entry_price: float,
                             usdt_size: float, signal_score: float) -> Position:
        if side == "BUY":
            tp = entry_price * (1 + config.take_profit_pct)
            sl = entry_price * (1 - config.stop_loss_pct)
        else:
            tp = entry_price * (1 - config.take_profit_pct)
            sl = entry_price * (1 + config.stop_loss_pct)

        pos = Position(
            id=self._next_id(),
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=usdt_size,
            tp_price=tp,
            sl_price=sl,
            opened_at=time.time(),
            signal_score=signal_score,
            current_price=entry_price,
        )
        async with self._lock:
            self._positions[pos.id] = pos
        logger.info(
            f"[ORDER] OPEN {side} {symbol} @ {entry_price:.4f} | "
            f"TP={tp:.4f} SL={sl:.4f} size={usdt_size:.2f}$"
        )
        return pos

    async def close_position(self, pos_id: str, exit_price: float, reason: str) -> Optional[Position]:
        async with self._lock:
            pos = self._positions.pop(pos_id, None)
        if pos is None:
            return None
        pos.update_price(exit_price)
        logger.info(
            f"[ORDER] CLOSE {pos.symbol} [{reason}] "
            f"PnL={pos.pnl:+.4f}$ ({pos.pnl_pct:+.3%}) "
            f"hold={pos.hold_seconds:.0f}s"
        )
        return pos

    async def get_positions(self) -> List[Position]:
        async with self._lock:
            return list(self._positions.values())

    def update_all_prices(self, prices: Dict[str, float]):
        for pos in self._positions.values():
            if pos.symbol in prices:
                pos.update_price(prices[pos.symbol])


order_manager = OrderManager()
