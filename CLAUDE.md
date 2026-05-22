# CLAUDE.md — Agent Shopify Sourcing & Boutique Futuriste

> **Mission** : Construire un agent autonome qui détecte les produits gagnants du marché en temps réel, les importe automatiquement sur une boutique Shopify au design futuriste, et optimise chaque fiche produit pour maximiser la conversion.

---

## Architecture globale

```
AGENT ORCHESTRATEUR (n8n)
├── MARKET SCOUT  (Trends API, TikTok, AliExpress)
├── PRICING AGENT (Concurrents, Meta Ads Library)
├── SOURCING AGENT (AliExpress, CJ, Spocket)
├── CONTENT AGENT  (Claude API — Copy + SEO)
├── SHOPIFY IMPORT (Admin API 2025-01)
└── BOUTIQUE LIVE  (Thème custom dark/néon)
```

## Scoring produit (0–100)

```
Score = Tendance × 0.30 + Marge × 0.25 + Saturation_inverse × 0.20
      + Wow_factor × 0.15 + Facilité_logistique × 0.10
```

Seuil : score ≥ 70 → pipeline | marge nette ≥ 30% → import

## Modèles Claude utilisés

- **Scoring + copywriting** : `claude-sonnet-4-6`
- **Traduction reviews** : `claude-haiku-4-5-20251001`
- **Réécriture copy (optimisation)** : `claude-sonnet-4-6`

## Structure du repo

```
├── n8n-workflows/          6 workflows complets (JSON n8n)
├── shopify-theme/          Thème futuriste dark/néon
│   ├── layout/theme.liquid
│   ├── sections/           Hero, grille produits, page produit
│   ├── assets/             global.css, animations.js, cursor.js
│   └── config/settings_schema.json
├── prompts/                Prompts système (copywriter, analyst, judge)
├── data/airtable-schema.md Structure base de données produits
└── README.md               Démarrage rapide + credentials
```

## Règles de développement

- Tous les tokens API dans les credentials n8n, jamais en dur
- Rate limit Shopify : 40 req/s burst, 2 req/s soutenu
- Produits santé/médical/nutrition → validation humaine obligatoire
- Draft par défaut, publication auto uniquement si score ≥ 85
- Langue : français FR/CH, tutoiement, pas de superlatifs gratuits

## Contexte CH

- Devise : CHF (EUR pour expansion)
- Paiement : Twint obligatoire
- Livraison : Swiss Post + DDP EU→CH
- TVA : seuil CHF 100k/an
