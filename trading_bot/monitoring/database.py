"""
SQLite persistence for open and closed trades.
"""
import aiosqlite
import logging

from trading_bot.config import config

log = logging.getLogger(__name__)

CREATE_OPEN = """
CREATE TABLE IF NOT EXISTS open_trades (
    id TEXT PRIMARY KEY,
    symbol TEXT,
    side TEXT,
    entry_price REAL,
    size_quote REAL,
    take_profit REAL,
    stop_loss REAL,
    opened_at REAL,
    signal_score REAL
)
"""

CREATE_CLOSED = """
CREATE TABLE IF NOT EXISTS closed_trades (
    id TEXT PRIMARY KEY,
    symbol TEXT,
    side TEXT,
    entry_price REAL,
    exit_price REAL,
    size_quote REAL,
    pnl REAL,
    pnl_pct REAL,
    hold_seconds REAL,
    exit_reason TEXT,
    opened_at REAL,
    closed_at REAL
)
"""


class TradeDB:
    def __init__(self):
        self.db_path = config.db_path
        self.saved_count = 0

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_OPEN)
            await db.execute(CREATE_CLOSED)
            await db.commit()
        log.info("[DB] Initialized: %s", self.db_path)

    async def save_open(self, pos) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO open_trades VALUES (?,?,?,?,?,?,?,?,?)",
                (pos.id, pos.symbol, pos.side, pos.entry_price, pos.size_quote,
                 pos.take_profit, pos.stop_loss, pos.opened_at, pos.signal_score),
            )
            await db.commit()

    async def save_closed(self, trade) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM open_trades WHERE id=?", (trade.id,))
            await db.execute(
                "INSERT OR REPLACE INTO closed_trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (trade.id, trade.symbol, trade.side, trade.entry_price, trade.exit_price,
                 trade.size_quote, trade.pnl, trade.pnl_pct, trade.hold_seconds,
                 trade.exit_reason, trade.opened_at, trade.closed_at),
            )
            await db.commit()
        self.saved_count += 1

    async def get_stats(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*), SUM(pnl), AVG(pnl_pct) FROM closed_trades") as cur:
                row = await cur.fetchone()
            async with db.execute("SELECT COUNT(*) FROM closed_trades WHERE pnl > 0") as cur:
                wins = (await cur.fetchone())[0]
        total = row[0] or 0
        return {
            "total_closed": total,
            "total_pnl": row[1] or 0.0,
            "avg_pnl_pct": (row[2] or 0.0) * 100,
            "win_rate": wins / total if total > 0 else 0.0,
        }
