"""Stratégie principale — Machine à Cache HF Scalper"""
import asyncio
import logging
import time

from trading_bot.config import config
from trading_bot.data.price_fetcher import get_ohlcv, get_spread_pct, LAST_PRICES
from trading_bot.analysis.technical import compute_signal
from trading_bot.analysis.signals import compute_final_signal
from trading_bot.execution.paper_trader import open_trade, check_and_close_positions
from trading_bot.strategy.risk_manager import risk_manager

logger = logging.getLogger(__name__)

# Evite d'ouvrir 2 positions sur le même symbole en même temps
_symbol_cooldowns: dict = {}
SYMBOL_COOLDOWN = 10   # secondes entre 2 trades sur le même symbole


async def _scan_symbol(symbol: str):
    """Analyse un symbole et déclenche un trade si signal fort."""
    now = time.time()
    if now < _symbol_cooldowns.get(symbol, 0):
        return

    spread = get_spread_pct(symbol)
    if spread > config.max_spread_pct:
        return

    ohlcv = get_ohlcv(symbol)
    if len(ohlcv) < 30:
        return

    tech = compute_signal(symbol, ohlcv)
    if tech is None:
        return

    signal = compute_final_signal(tech)
    if signal is None:
        return

    side = "BUY" if signal.direction > 0 else "SELL"
    pos = await open_trade(symbol, side, signal.final_score)
    if pos:
        _symbol_cooldowns[symbol] = now + SYMBOL_COOLDOWN


async def scalper_loop():
    """Boucle principale : scan de tous les marchés toutes les N secondes."""
    logger.info(f"[SCALPER] Démarrage sur {len(config.symbols)} marchés")
    while True:
        try:
            # Mise à jour des prix dans le risk manager
            can, _ = risk_manager.can_trade()

            # Check exit de positions existantes
            await check_and_close_positions()

            if can:
                # Scan de tous les marchés en parallèle
                tasks = [_scan_symbol(s) for s in config.symbols]
                await asyncio.gather(*tasks, return_exceptions=True)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"[SCALPER] Erreur boucle: {e}")

        await asyncio.sleep(config.scan_interval)
