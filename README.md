# BotBoutique — Telegram Shop + Machine à Cache Trading Bot

---

## 🤖 Machine à Cache — Bot de Trading Haute Fréquence

Bot de trading automatique inspiré de [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader), conçu pour faire de nombreuses micro-transactions par seconde sur plusieurs marchés crypto simultanément.

### Fonctionnalités
- **HF Scalping** : Scan de 10 marchés toutes les secondes (BTC, ETH, SOL, BNB, XRP…)
- **Analyse technique** : RSI, MACD, Bollinger Bands, EMA via `pandas-ta`
- **Analyse sentiment** : News crypto en temps réel (RSS + Alpha Vantage) analysées par Claude Haiku
- **Gestion du risque** : Stop-loss, take-profit, drawdown max, limite de perte journalière
- **Paper trading** : Mode simulation avec capital virtuel (argent réel optionnel)
- **Dashboard live** : Interface console temps-réel avec `rich`
- **Rapports Telegram** : Alertes et rapports P&L toutes les heures

### Démarrage rapide

```bash
# 1. Cloner et installer
pip install -r requirements.txt

# 2. Configurer
cp .env.example .env
# Editer .env : mettre ton capital, tes clés API, etc.

# 3. Lancer (paper trading par défaut)
python -m trading_bot.main
```

### Variables d'environnement clés

| Variable | Défaut | Description |
|---|---|---|
| `INITIAL_CAPITAL` | `10000` | Capital de départ (USDT) |
| `PAPER_TRADING` | `true` | Simulation ou argent réel |
| `ANTHROPIC_API_KEY` | — | Claude Haiku pour le sentiment |
| `ALPHA_VANTAGE_KEY` | — | News API (gratuit 25 req/j) |
| `BINANCE_API_KEY` | — | Optionnel en paper trading |

### Architecture

```
trading_bot/
├── main.py               # Orchestrateur asyncio
├── config.py             # Configuration centralisée
├── data/
│   ├── price_fetcher.py  # WebSocket Binance (ccxt)
│   ├── news_fetcher.py   # RSS + Alpha Vantage
│   └── market_intel.py   # Agrégation marché
├── analysis/
│   ├── technical.py      # RSI, MACD, BB, EMA
│   ├── sentiment.py      # Claude Haiku sentiment
│   └── signals.py        # Score composite final
├── strategy/
│   ├── scalper.py        # Boucle principale HF
│   └── risk_manager.py   # Gestion capital & risque
├── execution/
│   ├── paper_trader.py   # Moteur paper trading
│   └── order_manager.py  # Cycle de vie des ordres
└── monitoring/
    ├── dashboard.py      # Dashboard rich
    └── database.py       # SQLite logs trades
```

### Stratégie "Machine à Cache"
- Taille par trade : 2% du capital
- Take Profit : +0.3% | Stop Loss : -0.15%
- Durée max : 90 secondes
- Cooldown après 3 pertes consécutives (5 min)
- Pause automatique si drawdown > 10%

---

## 🛍️ Bot Telegram Boutique de Services

### Description
Bot Telegram en Python proposant plusieurs services avec boutons visuels, paiement en Solana et support direct.

## Services proposés
1. **Spam sur lien** : 25€ / 1k
2. **Technique Pristelle** : 50€ (3 SIM remboursables)
3. **Logs (Facebook, Amazon, Netflix, Mobiax)** : 10€ par log

## Paiement
- Paiement en crypto : **Solana (SOL)**
- Adresse par défaut : `DVaoLjuk8qsc3KbM84JoCHNSFLuVpwtLsD6ac6jWuzWx`

## Déploiement rapide sur Render
1. Décompressez le projet et poussez le dossier sur un dépôt GitHub.
2. Ouvrez [Render](https://render.com), cliquez sur **New + > Web Service**.
3. Sélectionnez **Deploy via render.yaml**, puis uploadez ce projet.
4. Dans **Environment**, ajoutez :
   - `BOT_TOKEN` = Votre token Telegram
   - `SUPPORT_USERNAME` = Votre username Telegram de support
   - `SOLANA_ADDRESS` = Votre adresse de dépôt Solana
5. Déployez : Render installera les dépendances et lancera `python bot.py`.

## Local (facultatif)
```bash
pip install -r requirements.txt
export BOT_TOKEN="votre_token"
export SUPPORT_USERNAME="blackdjdj"
export SOLANA_ADDRESS="votre_adresse_sol"
python bot.py
```

## Support
Contacter @{SUPPORT_USERNAME} sur Telegram pour toute question.
