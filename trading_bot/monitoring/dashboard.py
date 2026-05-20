"""Dashboard console temps-réel avec la librairie rich"""
import asyncio
import time
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from trading_bot.config import config
from trading_bot.execution.order_manager import order_manager
from trading_bot.strategy.risk_manager import risk_manager
from trading_bot.monitoring.database import db
from trading_bot.analysis.sentiment import get_sentiment
from trading_bot.data.price_fetcher import LAST_PRICES

console = Console()
_start_time = time.time()


def _color_pnl(value: float) -> str:
    if value > 0:
        return f"[green]+{value:.4f}$[/green]"
    if value < 0:
        return f"[red]{value:.4f}$[/red]"
    return f"[white]{value:.4f}$[/white]"


def _color_pct(value: float) -> str:
    pct = value * 100
    if pct > 0:
        return f"[green]+{pct:.3f}%[/green]"
    if pct < 0:
        return f"[red]{pct:.3f}%[/red]"
    return f"[white]{pct:.3f}%[/white]"


async def _build_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="positions", ratio=2),
        Layout(name="stats", ratio=1),
    )

    # --- HEADER ---
    risk = risk_manager.get_stats()
    uptime = int(time.time() - _start_time)
    h, m, s = uptime // 3600, (uptime % 3600) // 60, uptime % 60
    mode = "[yellow]PAPER[/yellow]" if config.paper_trading else "[red bold]LIVE[/red bold]"
    sentiment = get_sentiment()
    sent_color = "green" if sentiment.score > 0.2 else "red" if sentiment.score < -0.2 else "yellow"
    header_text = (
        f" [bold cyan]MACHINE À CACHE[/bold cyan] | Mode: {mode} | "
        f"Capital: [bold]{risk['capital']:.2f}$[/bold] | "
        f"Drawdown: [red]{risk['drawdown']:.2%}[/red] | "
        f"Sentiment: [{sent_color}]{sentiment.score:+.2f} {sentiment.label}[/{sent_color}] | "
        f"Uptime: {h:02d}:{m:02d}:{s:02d}"
    )
    layout["header"].update(Panel(Text.from_markup(header_text), style="bold"))

    # --- POSITIONS OUVERTES ---
    positions = await order_manager.get_positions()
    pos_table = Table(box=box.SIMPLE, expand=True, show_header=True, header_style="bold cyan")
    pos_table.add_column("ID", width=10)
    pos_table.add_column("Symbole", width=12)
    pos_table.add_column("Côté", width=6)
    pos_table.add_column("Entrée", width=12)
    pos_table.add_column("Actuel", width=12)
    pos_table.add_column("P&L", width=14)
    pos_table.add_column("Hold", width=8)
    pos_table.add_column("TP", width=12)
    pos_table.add_column("SL", width=12)

    for pos in sorted(positions, key=lambda p: p.opened_at, reverse=True):
        price = LAST_PRICES.get(pos.symbol, pos.current_price)
        pos.update_price(price)
        side_color = "green" if pos.side == "BUY" else "red"
        hold = int(pos.hold_seconds)
        pos_table.add_row(
            pos.id,
            pos.symbol,
            f"[{side_color}]{pos.side}[/{side_color}]",
            f"{pos.entry_price:.4f}",
            f"{price:.4f}",
            _color_pnl(pos.pnl),
            f"{hold}s",
            f"[dim]{pos.tp_price:.4f}[/dim]",
            f"[dim]{pos.sl_price:.4f}[/dim]",
        )

    if not positions:
        pos_table.add_row("—", "En attente de signaux...", "", "", "", "", "", "", "")

    layout["positions"].update(Panel(pos_table, title=f"[cyan]Positions ouvertes ({len(positions)})[/cyan]"))

    # --- STATS ---
    stats = await db.get_today_stats()
    win_rate = stats["wins"] / stats["trades"] * 100 if stats["trades"] > 0 else 0
    risk_stats = risk_manager.get_stats()

    stats_table = Table(box=box.SIMPLE, expand=True, show_header=False)
    stats_table.add_column("Clé", style="cyan")
    stats_table.add_column("Valeur", justify="right")

    stats_table.add_row("Trades aujourd'hui", str(stats["trades"]))
    stats_table.add_row("Gagnants", f"[green]{stats['wins']}[/green]")
    stats_table.add_row("Perdants", f"[red]{stats['losses']}[/red]")
    stats_table.add_row("Win Rate", f"{'[green]' if win_rate >= 50 else '[red]'}{win_rate:.1f}%{'[/green]' if win_rate >= 50 else '[/red]'}")
    stats_table.add_row("P&L net today", _color_pnl(stats["net_pnl"]))
    stats_table.add_row("Frais payés", f"[dim]{stats['total_fees']:.4f}$[/dim]")
    stats_table.add_row("Capital total", f"[bold]{risk_stats['capital']:.2f}$[/bold]")
    stats_table.add_row("Peak capital", f"{risk_stats['peak']:.2f}$")
    stats_table.add_row("Drawdown", f"[red]{risk_stats['drawdown']:.2%}[/red]")
    stats_table.add_row("Perte/jour", f"{risk_stats['daily_loss_pct']:.2%} / {config.max_daily_loss_pct:.0%}")
    stats_table.add_row("Pertes consécutives", str(risk_stats['consecutive_losses']))

    halted = risk_stats["trading_halted"]
    status = "[red bold]HALTED[/red bold]" if halted else "[green bold]ACTIF[/green bold]"
    stats_table.add_row("Statut", status)

    layout["stats"].update(Panel(stats_table, title="[cyan]Statistiques[/cyan]"))

    # --- FOOTER ---
    layout["footer"].update(Panel(
        Text.from_markup(
            f" Marchés: [bold]{', '.join(config.symbols[:6])}[/bold]... | "
            f"Scan: {config.scan_interval}s | "
            f"TP: {config.take_profit_pct:.1%} | SL: {config.stop_loss_pct:.1%} | "
            f"Max positions: {config.max_concurrent_positions} | "
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        ),
        style="dim"
    ))

    return layout


async def dashboard_loop():
    """Boucle du dashboard — rafraîchit toutes les secondes."""
    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            try:
                layout = await _build_layout()
                live.update(layout)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                console.print(f"[red]Dashboard error: {e}[/red]")
            await asyncio.sleep(1.0)
