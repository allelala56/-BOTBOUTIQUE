"""Gestion du risque — sizing, drawdown, cooldowns"""
import logging
import time
from dataclasses import dataclass, field
from typing import Dict

from trading_bot.config import config

logger = logging.getLogger(__name__)


@dataclass
class RiskState:
    capital: float
    peak_capital: float
    daily_loss: float          # perte nette du jour (valeur positive = perte)
    consecutive_losses: int
    cooldown_until: float      # timestamp fin de cooldown
    daily_pause_until: float   # timestamp fin de pause journalière
    trading_halted: bool       # drawdown max atteint
    open_positions_count: int

    @property
    def current_drawdown(self) -> float:
        if self.peak_capital == 0:
            return 0.0
        return (self.peak_capital - self.capital) / self.peak_capital

    @property
    def daily_loss_pct(self) -> float:
        initial = config.initial_capital
        if initial == 0:
            return 0.0
        return self.daily_loss / initial


class RiskManager:
    def __init__(self):
        self.state = RiskState(
            capital=config.initial_capital,
            peak_capital=config.initial_capital,
            daily_loss=0.0,
            consecutive_losses=0,
            cooldown_until=0.0,
            daily_pause_until=0.0,
            trading_halted=False,
            open_positions_count=0,
        )

    def can_trade(self) -> tuple[bool, str]:
        now = time.time()
        s = self.state

        if s.trading_halted:
            return False, f"HALTED: drawdown {s.current_drawdown:.1%} > {config.max_drawdown_pct:.1%}"

        if now < s.daily_pause_until:
            remaining = int(s.daily_pause_until - now)
            return False, f"DAILY PAUSE: {remaining//60}m{remaining%60:02d}s restantes"

        if now < s.cooldown_until:
            remaining = int(s.cooldown_until - now)
            return False, f"COOLDOWN: {remaining}s ({s.consecutive_losses} pertes consécutives)"

        if s.open_positions_count >= config.max_concurrent_positions:
            return False, f"MAX POSITIONS: {s.open_positions_count}/{config.max_concurrent_positions}"

        if s.daily_loss_pct >= config.max_daily_loss_pct:
            s.daily_pause_until = now + 4 * 3600
            return False, f"DAILY LOSS LIMIT: {s.daily_loss_pct:.1%}"

        if s.current_drawdown >= config.max_drawdown_pct:
            s.trading_halted = True
            return False, f"DRAWDOWN LIMIT: {s.current_drawdown:.1%}"

        return True, "OK"

    def position_size(self, price: float, volatility_factor: float = 1.0) -> float:
        """Calcule la taille de position en USDT, ajustée à la volatilité."""
        base = self.state.capital * config.max_position_pct
        adjusted = base / max(volatility_factor, 0.5)
        return round(min(adjusted, self.state.capital * 0.05), 2)

    def on_trade_open(self):
        self.state.open_positions_count += 1

    def on_trade_close(self, pnl: float):
        s = self.state
        s.open_positions_count = max(0, s.open_positions_count - 1)
        s.capital += pnl
        s.peak_capital = max(s.peak_capital, s.capital)

        if pnl < 0:
            s.daily_loss += abs(pnl)
            s.consecutive_losses += 1
            if s.consecutive_losses >= config.max_consecutive_losses:
                s.cooldown_until = time.time() + config.consecutive_loss_cooldown
                logger.warning(
                    f"[RISK] {s.consecutive_losses} pertes consécutives → cooldown "
                    f"{config.consecutive_loss_cooldown}s"
                )
        else:
            s.consecutive_losses = 0

    def reset_daily(self):
        """Appelé au début de chaque journée."""
        self.state.daily_loss = 0.0
        self.state.daily_pause_until = 0.0

    def get_stats(self) -> dict:
        s = self.state
        return {
            "capital": s.capital,
            "peak": s.peak_capital,
            "drawdown": s.current_drawdown,
            "daily_loss_pct": s.daily_loss_pct,
            "consecutive_losses": s.consecutive_losses,
            "open_positions": s.open_positions_count,
            "trading_halted": s.trading_halted,
        }


risk_manager = RiskManager()
