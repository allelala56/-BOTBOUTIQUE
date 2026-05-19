"""
Real-time console dashboard using the `rich` library.
Refreshes every second with live P&L, open positions, and stats.
"""
import asyncio
import time
from datetime import datetime

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from trading_bot.config import config
from trading_bot.analysis.sentiment import get_cached_sentiment
from trading_bot.data.price_fetcher import get_latest_price

console = Console()


def _render_header(stats: dict, risk_state) -> Panel:
    pnl = stats.get("total_pnl", 0.0)
    capital = stats.get("capital", config.initial_capital)
    unrealized = stats.get("unrealized_pnl", 0.0)
    pnl_color = "green" if pnl >= 0 else "red"
    unr_color = "green" if unrealized >= 0 else "red"

    sentiment_score, sentiment_label = get_cached_sentiment()
    sent_color = "green" if sentiment_score > 0.1 else "red" if sentiment_score < -0.1 else "yellow"

    initial = config.initial_capital
    total_return = (capital - initial) / initial * 100

    text = Text()
    text.append("  ██  MACHINE À CACHE  ██  ", style="bold cyan")
    text.append(f"  [{datetime.now().strftime('%H:%M:%S')}]\n\n", style="dim")
    text.append(f"  Capital : ", style="bold")
    text.append(f"{capital:,.2f} USDT ", style="bold white")
    text.append(f"({total_return:+.2f}%)\n", style=pnl_color)
    text.append(f"  P&L réalisé  : ", style="bold")
    text.append(f"{pnl:+.4f} USDT\n", style=pnl_color)
    text.append(f"  P&L non réalisé : ", style="bold")
    text.append(f"{unrealized:+.4f} USDT\n", style=unr_color)
    text.append(f"  Perte jour   : ", style="bold")
    text.append(f"{stats.get('daily_pnl', 0.0):+.4f} USDT\n", style="white")
    text.append(f"  Drawdown     : ", style="bold")
    text.append(f"{stats.get('drawdown', 0.0):.2%}\n", style="white")
    text.append(f"  Win rate     : ", style="bold")
    text.append(f"{stats.get('win_rate', 0.0):.1%}  ", style="white")
    text.append(f"({stats.get('wins', 0)}W / {stats.get('losses', 0)}L)", style="dim")
    text.append(f"\n  Sentiment    : ", style="bold")
    text.append(f"{sentiment_label} ({sentiment_score:+.2f})", style=sent_color)
    text.append(f"  |  Positions ouvertes : ", style="bold")
    text.append(f"{stats.get('open_positions', 0)}/{config.risk.max_concurrent_positions}\n", style="cyan")

    mode = "[bold red]LIVE MONEY[/bold red]" if not config.paper_trading else "[bold green]PAPER TRADING[/bold green]"
    return Panel(text, title=f"[bold cyan]Machine à Cache[/bold cyan] — {mode}", border_style="cyan")


def _render_positions(positions: dict) -> Panel:
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    table.add_column("ID", width=8)
    table.add_column("Symbole", width=12)
    table.add_column("Côté", width=6)
    table.add_column("Entrée", justify="right", width=14)
    table.add_column("Actuel", justify="right", width=14)
    table.add_column("P&L", justify="right", width=12)
    table.add_column("P&L %", justify="right", width=8)
    table.add_column("TP", justify="right", width=14)
    table.add_column("SL", justify="right", width=14)
    table.add_column("Tps", justify="right", width=8)

    for pos in positions.values():
        current = get_latest_price(pos.symbol)
        pnl = pos.pnl(current) if current > 0 else 0
        pnl_pct = pos.pnl_pct(current) * 100 if current > 0 else 0
        color = "green" if pnl >= 0 else "red"
        hold = int(time.time() - pos.opened_at)
        side_color = "cyan" if pos.side == "BUY" else "magenta"

        table.add_row(
            pos.id,
            pos.symbol.replace("/USDT", ""),
            Text(pos.side, style=side_color),
            f"{pos.entry_price:.6f}",
            f"{current:.6f}" if current > 0 else "—",
            Text(f"{pnl:+.4f}", style=color),
            Text(f"{pnl_pct:+.2f}%", style=color),
            f"{pos.take_profit:.6f}",
            f"{pos.stop_loss:.6f}",
            f"{hold}s",
        )

    title = f"[bold]Positions Ouvertes[/bold] ({len(positions)})"
    return Panel(table, title=title, border_style="magenta")


def _render_recent_trades(history: list) -> Panel:
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold yellow")
    table.add_column("ID", width=8)
    table.add_column("Symbole", width=12)
    table.add_column("Côté", width=6)
    table.add_column("Entrée", justify="right", width=14)
    table.add_column("Sortie", justify="right", width=14)
    table.add_column("P&L", justify="right", width=12)
    table.add_column("P&L %", justify="right", width=8)
    table.add_column("Durée", justify="right", width=8)
    table.add_column("Raison", width=8)

    recent = list(reversed(history[-15:]))
    for trade in recent:
        color = "green" if trade.pnl > 0 else "red"
        side_color = "cyan" if trade.side == "BUY" else "magenta"
        table.add_row(
            trade.id,
            trade.symbol.replace("/USDT", ""),
            Text(trade.side, style=side_color),
            f"{trade.entry_price:.6f}",
            f"{trade.exit_price:.6f}",
            Text(f"{trade.pnl:+.4f}", style=color),
            Text(f"{trade.pnl_pct * 100:+.2f}%", style=color),
            f"{int(trade.hold_seconds)}s",
            trade.exit_reason,
        )

    return Panel(table, title="[bold]15 Derniers Trades[/bold]", border_style="yellow")


class Dashboard:
    def __init__(self, paper_trader, risk_manager):
        self.trader = paper_trader
        self.risk = risk_manager

    async def run(self) -> None:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=12),
            Layout(name="positions", size=16),
            Layout(name="history"),
        )

        with Live(layout, console=console, refresh_per_second=1, screen=True):
            while True:
                stats = self.trader.stats()
                layout["header"].update(_render_header(stats, self.risk.state))
                layout["positions"].update(_render_positions(self.trader.positions))
                layout["history"].update(_render_recent_trades(self.trader.history))
                await asyncio.sleep(1)
