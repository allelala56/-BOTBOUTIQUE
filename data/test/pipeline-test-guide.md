# Guide de test manuel du pipeline n8n

Procédure pour valider le pipeline complet avant d'activer les crons automatiques.

---

## Prérequis

- n8n.cloud configuré avec les 6 workflows importés
- Tous les credentials renseignés (voir README.md)
- Shopify en mode "Boutique de développement" ou plan Basic
- Airtable base créée avec les 4 tables (voir `data/airtable-schema.md`)

---

## Étape 1 — Tester le Content Agent seul (le plus rapide)

C'est le nœud le plus critique (Claude API). Tester en premier.

1. Ouvrir le workflow `04_content_agent` dans n8n
2. Ajouter un node **Manual Trigger** en début de workflow
3. Coller le payload suivant dans ce node :

```json
{
  "id": "test-001",
  "title": "Organisateur de câbles magnétique bureau — Lot de 5",
  "niche": "bureau-maison",
  "score": 82,
  "pricing": {
    "target_price_chf": 28.90,
    "crossed_price_chf": 44.90,
    "net_margin_pct": 38.2
  },
  "supplier": {
    "source": "aliexpress",
    "id": "12345678",
    "price_chf": 6.80,
    "shipping_days_eu": 8,
    "images": [
      "https://ae01.alicdn.com/kf/sample-1.jpg",
      "https://ae01.alicdn.com/kf/sample-2.jpg"
    ]
  },
  "reviews_raw": [
    { "rating": 5, "text_original": "Great product, fast shipping!", "author": "John D.", "country": "CH" },
    { "rating": 5, "text_original": "Exactly what I needed, very clean design", "author": "Marie L.", "country": "FR" },
    { "rating": 4, "text_original": "Good quality but delivery took 10 days", "author": "Thomas B.", "country": "DE" }
  ]
}
```

4. Exécuter et vérifier que Claude retourne un JSON valide avec tous les champs
5. Vérifier la traduction des reviews (node `Claude — Traduire reviews en FR`)

**Résultat attendu** : JSON complet avec titre FR, body_html, 5 bullet points, 5 FAQ, urgency_text, garantie, etc.

---

## Étape 2 — Tester le Shopify Import seul

1. Ouvrir le workflow `05_shopify_import`
2. Ajouter un node **Manual Trigger**
3. Coller le résultat complet de l'Étape 1 (enrichi avec `content`)
4. Exécuter

**Vérifier dans Shopify** :
- [ ] Produit créé en statut "Draft" (score < 85)
- [ ] Images uploadées (vérifier via Admin → Produits → [titre])
- [ ] Prix et prix barré corrects
- [ ] Métafields visibles (urgency_text, guarantee_text, shipping_eta_ch)
- [ ] Stock défini à 100
- [ ] Tags Shopify corrects

---

## Étape 3 — Tester le Market Scout manuellement

1. Ouvrir workflow `01_market_scout`
2. Remplacer le node **Cron Trigger** par un **Manual Trigger**
3. Injecter les 5 produits de `data/test/mock-products.json` directement dans le node **Agréger les signaux**

**Résultats attendus par produit** :

| ID | Score attendu | Verdict |
|---|---|---|
| test-001 | ~82 | VALIDE |
| test-002 | ~74 | VALIDE |
| test-003 | ~65 | REJETE (alerte santé) |
| test-004 | ~44 | REJETE (saturé) |
| test-005 | ~78 | VALIDE |

Ajuster les seuils du prompt si les scores s'écartent de > 10 points.

---

## Étape 4 — Test pipeline bout en bout

Une fois les étapes 1–3 validées :

1. Prendre le produit `test-001` (score le plus élevé)
2. Déclencher manuellement dans l'ordre :
   - `03_sourcing_agent` → vérifie la sélection fournisseur
   - `04_content_agent` → vérifie le copy
   - `05_shopify_import` → vérifie l'import
3. Aller dans Airtable et vérifier que toutes les colonnes sont renseignées
4. Aller dans Shopify Admin et vérifier la fiche produit complète

---

## Étape 5 — Activer les crons

Une fois le pipeline bout-en-bout validé sur 3 produits minimum :

1. Activer `01_market_scout` (cron 4×/jour)
2. Activer `06_optimization_loop` (cron quotidien 8h)
3. Laisser tourner 48h en mode surveillance

**Métriques à surveiller** :
- Taux de succès des executions n8n (objectif > 95%)
- Nombre de produits détectés par jour (objectif 5–15)
- Nombre de produits passant le seuil score 70 (objectif 20–30%)
- Erreurs API (rate limit Shopify, quota Anthropic)

---

## Erreurs fréquentes et solutions

| Erreur | Cause probable | Solution |
|---|---|---|
| `429 Too Many Requests` | Rate limit Shopify | Ajouter un node `Wait` de 1s entre les requêtes |
| `JSON parse error` | Claude n'a pas retourné un JSON valide | Ajouter un `try/catch` + retry dans le node Code |
| `401 Unauthorized` | Credential expiré | Renouveler le token dans n8n Credentials |
| `Image upload failed` | URL image inaccessible (AliExpress CDN) | Pré-télécharger via Cloudinary ou ImageKit |
| Airtable champ vide | Clé manquante dans le JSON | Vérifier la correspondance des noms de colonnes |

---

## Checklist avant passage en production

- [ ] Pipeline testé sur 5 produits manuels
- [ ] 0 erreur critique sur les 5 tests
- [ ] Reviews traduites correctement en français
- [ ] Fiches Shopify conformes au template (sections visibles, métafields OK)
- [ ] Airtable: tous les champs renseignés pour les 5 produits test
- [ ] Rate limits vérifiés (Shopify : 40 req/s, Anthropic : 60 req/min)
- [ ] Pages légales publiées sur Shopify (CGV, confidentialité, retours)
- [ ] Pixel Meta + TikTok installés et vérifiés
- [ ] Test d'achat complet (panier → paiement → confirmation) effectué
