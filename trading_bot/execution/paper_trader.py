"""
Paper trading engine: simulates trades on real market prices.
Applies realistic slippage and exchange fees.
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from trading_bot.config import config
from trading_bot.data.price_fetcher import get_latest_price

log = logging.getLogger(__name__)


@dataclass
class Position:
    id: str
    symbol: str
    side: str           # "BUY" | "SELL"
    entry_price: float
    size_quote: float   # invested amount in USDT
    size_base: float    # quantity in base asset
    opened_at: float    # unix timestamp
    take_profit: float
    stop_loss: float
    max_hold_until: float
    signal_score: float

    def pnl(self, current_price: float) -> float:
        if self.side == "BUY":
            return (current_price - self.entry_price) / self.entry_price * self.size_quote
        else:
            return (self.entry_price - current_price) / self.entry_price * self.size_quote

    def pnl_pct(self, current_price: float) -> float:
        if self.entry_price == 0:
            return 0.0
        if self.side == "BUY":
            return (current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - current_price) / self.entry_price


@dataclass
class ClosedTrade:
    id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size_quote: float
    pnl: float
    pnl_pct: float
    hold_seconds: float
    exit_reason: str    # "TP" | "SL" | "TIME" | "MANUAL"
    opened_at: float
    closed_at: float


class PaperTrader:
    def __init__(self, risk_manager):
        self.risk = risk_manager
        self.positions: Dict[str, Position] = {}
        self.history: List[ClosedTrade] = []

    def open_position(
        self,
        symbol: str,
        side: str,
        price: float,
        size_quote: float,
        signal_score: float,
    ) -> Optional[Position]:
        # Apply slippage
        if side == "BUY":
            fill_price = price * (1 + config.slippage_pct)
        else:
            fill_price = price * (1 - config.slippage_pct)

        # Apply taker fee on entry
        effective_quote = size_quote * (1 - config.fee_pct)
        size_base = effective_quote / fill_price if fill_price > 0 else 0

        tp_pct = config.risk.take_profit_pct
        sl_pct = config.risk.stop_loss_pct

        if side == "BUY":
            take_profit = fill_price * (1 + tp_pct)
            stop_loss   = fill_price * (1 - sl_pct)
        else:
            take_profit = fill_price * (1 - tp_pct)
            stop_loss   = fill_price * (1 + sl_pct)

        pos = Position(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            entry_price=fill_price,
            size_quote=size_quote,
            size_base=size_base,
            opened_at=time.time(),
            take_profit=take_profit,
            stop_loss=stop_loss,
            max_hold_until=time.time() + config.risk.max_hold_seconds,
            signal_score=signal_score,
        )
        self.positions[pos.id] = pos
        self.risk.on_trade_open()
        log.info(
            "[TRADE OPEN] %s %s @ %.6f | TP=%.6f SL=%.6f | size=%.2f USDT",
            side, symbol, fill_price, take_profit, stop_loss, size_quote,
        )
        return pos

    def close_position(self, pos_id: str, reason: str = "MANUAL") -> Optional[ClosedTrade]:
        pos = self.positions.pop(pos_id, None)
        if pos is None:
            return None

        current_price = get_latest_price(pos.symbol)
        if current_price <= 0:
            current_price = pos.entry_price  # fallback

        # Apply slippage on exit
        if pos.side == "BUY":
            exit_price = current_price * (1 - config.slippage_pct)
        else:
            exit_price = current_price * (1 + config.slippage_pct)

        raw_pnl = pos.pnl(exit_price)
        fee_exit = pos.size_quote * config.fee_pct
        net_pnl = raw_pnl - fee_exit

        hold_secs = time.time() - pos.opened_at
        pnl_pct = pos.pnl_pct(exit_price) - config.fee_pct * 2  # round-trip fees

        trade = ClosedTrade(
            id=pos.id,
            symbol=pos.symbol,
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            size_quote=pos.size_quote,
            pnl=net_pnl,
            pnl_pct=pnl_pct,
            hold_seconds=hold_secs,
            exit_reason=reason,
            opened_at=pos.opened_at,
            closed_at=time.time(),
        )
        self.history.append(trade)
        self.risk.on_trade_close(net_pnl)

        emoji = "✅" if net_pnl > 0 else "❌"
        log.info(
            "[TRADE CLOSE] %s %s %s @ %.6f → %.6f | PnL=%+.4f USDT (%+.2f%%) | %s",
            emoji, pos.side, pos.symbol, pos.entry_price, exit_price,
            net_pnl, pnl_pct * 100, reason,
        )
        return trade

    async def tick(self) -> None:
        """Check all open positions for TP/SL/time exits."""
        now = time.time()
        to_close = []
        for pos_id, pos in list(self.positions.items()):
            price = get_latest_price(pos.symbol)
            if price <= 0:
                continue

            if pos.side == "BUY":
                if price >= pos.take_profit:
                    to_close.append((pos_id, "TP"))
                elif price <= pos.stop_loss:
                    to_close.append((pos_id, "SL"))
            else:
                if price <= pos.take_profit:
                    to_close.append((pos_id, "TP"))
                elif price >= pos.stop_loss:
                    to_close.append((pos_id, "SL"))

            if now >= pos.max_hold_until:
                to_close.append((pos_id, "TIME"))

        already_closed = set()
        for pos_id, reason in to_close:
            if pos_id not in already_closed:
                self.close_position(pos_id, reason)
                already_closed.add(pos_id)

    def stats(self) -> dict:
        """Compute live P&L stats."""
        trades = self.history
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        total_pnl = sum(t.pnl for t in trades)
        win_rate = len(wins) / len(trades) if trades else 0.0

        unrealized = 0.0
        for pos in self.positions.values():
            p = get_latest_price(pos.symbol)
            if p > 0:
                unrealized += pos.pnl(p)

        return {
            "capital": self.risk.state.current_capital,
            "total_trades": len(trades),
            "open_positions": len(self.positions),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "unrealized_pnl": unrealized,
            "daily_pnl": self.risk.state.daily_pnl,
            "drawdown": self.risk.state.drawdown_pct(),
            "wins": len(wins),
            "losses": len(losses),
        }
