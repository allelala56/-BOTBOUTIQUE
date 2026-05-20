"""SQLite async — logging de tous les trades"""
import asyncio
import aiosqlite
from dataclasses import dataclass
from typing import Optional
from datetime import date

from trading_bot.config import config


@dataclass
class TradeRecord:
    id: Optional[int]
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    fee: float
    hold_seconds: float
    exit_reason: str
    opened_at: float
    closed_at: float
    signal_score: float


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS trades (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol       TEXT    NOT NULL,
    side         TEXT    NOT NULL,
    entry_price  REAL    NOT NULL,
    exit_price   REAL    NOT NULL,
    quantity     REAL    NOT NULL,
    pnl          REAL    NOT NULL,
    pnl_pct      REAL    NOT NULL,
    fee          REAL    NOT NULL,
    hold_seconds REAL    NOT NULL,
    exit_reason  TEXT    NOT NULL,
    opened_at    REAL    NOT NULL,
    closed_at    REAL    NOT NULL,
    signal_score REAL    NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_stats (
    date       TEXT PRIMARY KEY,
    trades     INTEGER DEFAULT 0,
    wins       INTEGER DEFAULT 0,
    losses     INTEGER DEFAULT 0,
    gross_pnl  REAL    DEFAULT 0,
    net_pnl    REAL    DEFAULT 0,
    total_fees REAL    DEFAULT 0
);
"""


class Database:
    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        self._conn = await aiosqlite.connect(config.db_path)
        await self._conn.executescript(_CREATE_SQL)
        await self._conn.commit()

    async def save_trade(self, trade: TradeRecord):
        async with self._lock:
            await self._conn.execute(
                """INSERT INTO trades
                   (symbol, side, entry_price, exit_price, quantity, pnl,
                    pnl_pct, fee, hold_seconds, exit_reason, opened_at, closed_at, signal_score)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (trade.symbol, trade.side, trade.entry_price, trade.exit_price,
                 trade.quantity, trade.pnl, trade.pnl_pct, trade.fee,
                 trade.hold_seconds, trade.exit_reason, trade.opened_at,
                 trade.closed_at, trade.signal_score)
            )
            today = str(date.today())
            win = 1 if trade.pnl > 0 else 0
            loss = 1 - win
            net = trade.pnl - trade.fee
            await self._conn.execute(
                """INSERT INTO daily_stats (date, trades, wins, losses, gross_pnl, net_pnl, total_fees)
                   VALUES (?, 1, ?, ?, ?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                     trades     = trades + 1,
                     wins       = wins + ?,
                     losses     = losses + ?,
                     gross_pnl  = gross_pnl + ?,
                     net_pnl    = net_pnl + ?,
                     total_fees = total_fees + ?""",
                (today, win, loss, trade.pnl, net, trade.fee,
                 win, loss, trade.pnl, net, trade.fee)
            )
            await self._conn.commit()

    async def get_today_stats(self) -> dict:
        today = str(date.today())
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT trades, wins, losses, net_pnl, total_fees FROM daily_stats WHERE date=?",
                (today,)
            )
            row = await cur.fetchone()
        if not row:
            return {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0, "total_fees": 0.0}
        return {"trades": row[0], "wins": row[1], "losses": row[2],
                "net_pnl": row[3], "total_fees": row[4]}

    async def close(self):
        if self._conn:
            await self._conn.close()


db = Database()
