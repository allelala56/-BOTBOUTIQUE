# BotBoutique — Agent IA Shopify Sourcing

Système end-to-end qui détecte les produits gagnants, les importe automatiquement sur Shopify avec des fiches optimisées, dans une boutique au design futuriste dark/néon.

## Structure du projet

```
├── n8n-workflows/          # 6 workflows n8n prêts à importer
│   ├── 01_market_scout     # Détection tendances (TikTok, Google Trends, AliExpress)
│   ├── 02_pricing_agent    # Analyse concurrence & calcul marge nette
│   ├── 03_sourcing_agent   # Sélection meilleur fournisseur (CJ, AliExpress, Spocket)
│   ├── 04_content_agent    # Copywriting complet via Claude API
│   ├── 05_shopify_import   # Import produit + images + reviews sur Shopify
│   └── 06_optimization_loop # Boucle quotidienne (rewrite, hero, archive)
│
├── shopify-theme/          # Thème Shopify futuriste (fork Dawn)
│   ├── layout/theme.liquid # Layout principal
│   ├── sections/           # Hero vidéo, grille produits, page produit
│   ├── assets/
│   │   ├── global.css      # Design system complet (variables, composants)
│   │   ├── animations.js   # Scroll reveal, typewriter, tilt 3D, FAQ
│   │   └── cursor.js       # Curseur néon custom avec traînée
│   └── config/settings_schema.json
│
├── prompts/                # Prompts système pour les agents Claude
│   ├── copywriter.md       # Génération fiche produit complète
│   ├── market_analyst.md   # Scoring produit (0–100)
│   └── product_judge.md    # Optimisation copy (boucle)
│
├── data/
│   └── airtable-schema.md  # Structure complète de la base Airtable
│
└── CLAUDE.md               # Documentation complète du projet
```

## Démarrage rapide

### 1. n8n.cloud

1. Créer un compte sur [n8n.cloud](https://n8n.cloud)
2. Importer chaque fichier JSON depuis `n8n-workflows/` via **Import workflow**
3. Configurer les credentials (voir ci-dessous)
4. Activer les workflows dans l'ordre 01 → 06

### 2. Credentials à configurer dans n8n

| Credential | Service | Où l'obtenir |
|---|---|---|
| `anthropicApiKey` | Claude API | console.anthropic.com |
| `shopifyAccessToken` | Shopify Admin API | Admin → Apps → Développement |
| `shopifyStoreDomain` | Shopify | `ta-boutique.myshopify.com` |
| `shopifyLocationId` | Shopify | Admin → Paramètres → Localisation |
| `airtableBaseId` | Airtable | URL de ta base Airtable |
| `aliexpressApiKey` | AliExpress Affiliate | portals.aliexpress.com |
| `cjDropshippingToken` | CJ Dropshipping | developers.cjdropshipping.com |
| `spocketToken` | Spocket | app.spocket.co/settings |
| `serpApiKey` | SerpAPI | serpapi.com/manage-api-key |
| `apifyToken` | Apify | console.apify.com/account/integrations |
| `metaAccessToken` | Meta Graph API | developers.facebook.com |
| `judgeMeToken` | Judge.me | judge.me/admin/settings |

### 3. Thème Shopify

1. Dans ton admin Shopify : **Boutique en ligne → Thèmes → Ajouter un thème**
2. Uploader les fichiers du dossier `shopify-theme/` (ou via Shopify CLI)
3. Configurer dans **Personnaliser le thème** → Paramètres du thème
4. Personnaliser les sections depuis l'éditeur visuel

### 4. Airtable

1. Créer une nouvelle base Airtable
2. Créer les 4 tables selon le schéma dans `data/airtable-schema.md`
3. Copier l'ID de ta base (URL : `airtable.com/appXXXXXXXX/...`)
4. Renseigner dans les credentials n8n

## Pipeline produit (flux complet)

```
Market Scout (cron 4×/jour)
    → Score Claude ≥ 70 ?
    → Pricing Agent (marge nette ≥ 30% ?)
    → Sourcing Agent (meilleur fournisseur)
    → Content Agent (Claude — copywriting complet)
    → Shopify Import (draft si score < 85, actif si ≥ 85)
    → Validation humaine (dashboard Airtable)
    → Publication

Optimization Loop (quotidien 8h00)
    → CVR < 1% + vues > 500 → Réécriture copy (Claude)
    → CVR ≥ 3% → Hero Product + scale budget
    → 0 vente en 14j → Archivage automatique
```

## KPIs cibles à 90 jours

| Métrique | Objectif |
|---|---|
| Produits actifs | 30–50 |
| Hero products | 2–3 |
| Taux de conversion | > 2% |
| AOV | > CHF 60 |
| ROAS | > 2.5 |
| Revenu mensuel | CHF 15k–30k |

## Notes contexte CH

- **Devise** : CHF par défaut, EUR pour l'expansion EU
- **Paiement** : Twint obligatoire pour le marché suisse
- **Livraison** : intégration Swiss Post + transitaire EU→CH (livraison DDP)
- **TVA** : seuil CHF 100k/an — inscription anticipée recommandée
- **nLPD** : conformité loi suisse sur la protection des données

## Roadmap

- [x] Phase 1 — Architecture et workflows n8n
- [x] Phase 1 — Thème Shopify futuriste
- [x] Phase 1 — Prompts agents Claude
- [ ] Phase 2 — Connexion APIs fournisseurs (AliExpress, CJ, Spocket)
- [ ] Phase 2 — Test pipeline sur 10 produits manuels
- [ ] Phase 3 — Design boutique finalisé (mobile-first)
- [ ] Phase 4 — Acquisition (Meta + TikTok Ads)
- [ ] Phase 5 — Scale + private label
