"""
Risk manager: position sizing, drawdown control, daily loss limits, cooldowns.
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from trading_bot.config import config

log = logging.getLogger(__name__)


@dataclass
class RiskState:
    initial_capital: float
    current_capital: float
    peak_capital: float
    daily_pnl: float = 0.0
    day_start_capital: float = 0.0
    day_start_ts: float = field(default_factory=time.time)
    consecutive_losses: int = 0
    cooldown_until: float = 0.0
    paused: bool = False
    pause_reason: str = ""
    open_positions: int = 0

    def drawdown_pct(self) -> float:
        if self.peak_capital <= 0:
            return 0.0
        return (self.peak_capital - self.current_capital) / self.peak_capital

    def daily_loss_pct(self) -> float:
        base = self.day_start_capital if self.day_start_capital > 0 else self.initial_capital
        return (self.day_start_capital - self.current_capital) / base

    def in_cooldown(self) -> bool:
        return time.time() < self.cooldown_until


class RiskManager:
    def __init__(self):
        self.state = RiskState(
            initial_capital=config.initial_capital,
            current_capital=config.initial_capital,
            peak_capital=config.initial_capital,
            day_start_capital=config.initial_capital,
        )
        self.cfg = config.risk

    def can_trade(self) -> tuple[bool, str]:
        """Returns (allowed, reason_if_not)."""
        if self.state.paused:
            return False, self.state.pause_reason

        if self.state.in_cooldown():
            remaining = int(self.state.cooldown_until - time.time())
            return False, f"Cooldown ({remaining}s restants)"

        if self.state.open_positions >= self.cfg.max_concurrent_positions:
            return False, f"Max positions atteint ({self.cfg.max_concurrent_positions})"

        return True, ""

    def check_limits(self) -> None:
        """Check drawdown and daily loss; pause trading if breached."""
        s = self.state

        # Reset daily tracking at midnight
        now = time.time()
        if now - s.day_start_ts > 86400:
            s.daily_pnl = 0.0
            s.day_start_capital = s.current_capital
            s.day_start_ts = now

        # Update peak
        if s.current_capital > s.peak_capital:
            s.peak_capital = s.current_capital

        drawdown = s.drawdown_pct()
        if drawdown >= self.cfg.max_drawdown_pct:
            s.paused = True
            s.pause_reason = f"Drawdown max atteint ({drawdown:.1%}) — arrêt total"
            log.critical("[RISK] %s", s.pause_reason)
            return

        daily_loss = s.daily_loss_pct()
        if daily_loss >= self.cfg.max_daily_loss_pct:
            s.cooldown_until = time.time() + 4 * 3600
            s.pause_reason = f"Perte journalière max ({daily_loss:.1%}) — pause 4h"
            log.warning("[RISK] %s", s.pause_reason)

    def position_size(self, price: float) -> float:
        """Calculate position size in quote currency."""
        if price <= 0:
            return 0.0
        capital = self.state.current_capital
        size_quote = capital * self.cfg.max_position_pct
        return size_quote

    def on_trade_open(self) -> None:
        self.state.open_positions += 1

    def on_trade_close(self, pnl: float) -> None:
        self.state.open_positions = max(0, self.state.open_positions - 1)
        self.state.current_capital += pnl
        self.state.daily_pnl += pnl

        if pnl < 0:
            self.state.consecutive_losses += 1
            if self.state.consecutive_losses >= self.cfg.consecutive_loss_cooldown:
                self.state.cooldown_until = time.time() + self.cfg.cooldown_seconds
                self.state.consecutive_losses = 0
                log.warning(
                    "[RISK] %d pertes consécutives — cooldown %ds",
                    self.cfg.consecutive_loss_cooldown,
                    self.cfg.cooldown_seconds,
                )
        else:
            self.state.consecutive_losses = 0

        self.check_limits()
