"""Moteur de paper trading — simule exécution avec slippage et fees"""
import logging
import time
from typing import Optional

from trading_bot.config import config
from trading_bot.execution.order_manager import order_manager, Position
from trading_bot.strategy.risk_manager import risk_manager
from trading_bot.monitoring.database import db, TradeRecord
from trading_bot.data.price_fetcher import get_price

logger = logging.getLogger(__name__)


def _simulate_fill(price: float, side: str) -> float:
    """Simule le slippage à l'exécution."""
    if side == "BUY":
        return price * (1 + config.slippage_pct)
    return price * (1 - config.slippage_pct)


async def open_trade(symbol: str, side: str, signal_score: float) -> Optional[Position]:
    """Ouvre une position simulée."""
    can, reason = risk_manager.can_trade()
    if not can:
        logger.debug(f"[PAPER] Skip {symbol}: {reason}")
        return None

    market_price = get_price(symbol)
    if not market_price:
        return None

    fill_price = _simulate_fill(market_price, side)
    usdt_size = risk_manager.position_size(fill_price)

    risk_manager.on_trade_open()
    pos = await order_manager.open_position(
        symbol=symbol, side=side, entry_price=fill_price,
        usdt_size=usdt_size, signal_score=signal_score
    )
    return pos


async def close_trade(pos_id: str, exit_price: float, reason: str):
    """Ferme une position simulée et enregistre le résultat."""
    fill_price = _simulate_fill(
        exit_price,
        "SELL" if (await _get_side(pos_id)) == "BUY" else "BUY"
    )
    pos = await order_manager.close_position(pos_id, fill_price, reason)
    if pos is None:
        return

    fee = pos.quantity * config.fee_pct * 2   # entrée + sortie
    net_pnl = pos.pnl - fee

    risk_manager.on_trade_close(net_pnl)

    record = TradeRecord(
        id=None,
        symbol=pos.symbol,
        side=pos.side,
        entry_price=pos.entry_price,
        exit_price=fill_price,
        quantity=pos.quantity,
        pnl=net_pnl,
        pnl_pct=pos.pnl_pct,
        fee=fee,
        hold_seconds=pos.hold_seconds,
        exit_reason=reason,
        opened_at=pos.opened_at,
        closed_at=time.time(),
        signal_score=pos.signal_score,
    )
    await db.save_trade(record)


async def _get_side(pos_id: str) -> str:
    positions = await order_manager.get_positions()
    for p in positions:
        if p.id == pos_id:
            return p.side
    return "BUY"


async def check_and_close_positions():
    """Vérifie toutes les positions ouvertes pour TP/SL/TIMEOUT."""
    positions = await order_manager.get_positions()
    for pos in positions:
        price = get_price(pos.symbol)
        if price:
            pos.update_price(price)
            reason = pos.should_close()
            if reason:
                await close_trade(pos.id, price, reason)
