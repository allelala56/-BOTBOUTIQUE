# Airtable — Structure de la base produits

Base : `BotBoutique — Pipeline Produits`

---

## Table 1 : `tblProductCandidates` — Candidats & pipeline

| Champ | Type | Description |
|---|---|---|
| `Title` | Texte court | Titre brut du fournisseur |
| `Source` | Sélection | `aliexpress` / `tiktok` / `google_trends` / `amazon` / `pinterest` |
| `Score` | Nombre (0–100) | Score global Market Scout |
| `Tendance` | Nombre (0–30) | Sous-score tendance |
| `Marge_potentielle` | Nombre (0–25) | Sous-score marge |
| `Saturation_inverse` | Nombre (0–20) | Sous-score saturation |
| `Wow_factor` | Nombre (0–15) | Sous-score wow |
| `Facilite_logistique` | Nombre (0–10) | Sous-score logistique |
| `Verdict` | Sélection | `VALIDE` / `REJETE` |
| `Niche` | Texte court | Catégorie (ex: maison-bureau, cuisine, sport) |
| `Image_URL` | URL | Image principale du fournisseur |
| `Video_URL` | URL | Vidéo produit (si disponible) |
| `Date_detection` | Date-heure | Timestamp de détection |
| `Status` | Sélection | Voir pipeline ci-dessous |
| `Prix_fournisseur_CHF` | Devise | Prix fournisseur brut |
| `Prix_fournisseur_reel` | Devise | Prix fournisseur confirmé après sourcing |
| `Prix_vente_suggere_CHF` | Devise | Prix suggéré par Market Scout |
| `Prix_vente_CHF` | Devise | Prix final après Pricing Agent |
| `Prix_barre_CHF` | Devise | Prix barré (compare_at_price) |
| `Marge_nette_pct` | Nombre | Marge nette projetée (%) |
| `Saturation` | Sélection | `VIERGE` / `CONCURRENTIEL` / `SATURE` |
| `Fournisseur` | Sélection | `aliexpress` / `cj_dropshipping` / `spocket` / `zendrop` |
| `Fournisseur_ID` | Texte court | ID produit chez le fournisseur |
| `Delai_livraison_EU` | Nombre | Jours de livraison vers EU/CH |
| `Nb_reviews` | Nombre | Nombre de reviews récupérées |
| `Titre_FR` | Texte court | Titre en français (généré par Claude) |
| `Meta_title` | Texte court | Meta title SEO |
| `Shopify_Product_ID` | Texte court | ID du produit sur Shopify |
| `Shopify_URL` | URL | URL de la fiche produit |
| `Date_import` | Date-heure | Timestamp d'import sur Shopify |
| `Pipeline_stage` | Texte court | Stage technique actuel |
| `Alerte_humaine` | Case à cocher | Nécessite validation manuelle |
| `Notes` | Texte long | Notes manuelles |

### Pipeline `Status` (valeurs ordonnées)

1. `Nouveau` — détecté par Market Scout
2. `Pricing OK — En attente sourcing`
3. `Sourcing OK — En attente content`
4. `Content OK — Prêt pour import Shopify`
5. `Importé — En attente validation`
6. `Publié automatiquement` (score ≥ 85)
7. `Rejeté` (à n'importe quelle étape)
8. `Archivé` (0 vente en 14j)

### Vues suggérées dans Airtable

- **Vue "À valider"** : filter `Status = Importé — En attente validation`, sort `Score DESC`
- **Vue "Pipeline actif"** : filter `Status != Rejeté AND Status != Archivé`
- **Vue "Hero Products"** : filter `Shopify_Product_ID != blank AND Marge_nette_pct >= 30`
- **Vue "Alertes humaines"** : filter `Alerte_humaine = true`

---

## Table 2 : `tblOptimizationLog` — Journal des optimisations

| Champ | Type | Description |
|---|---|---|
| `Product_ID` | Texte court | ID Shopify du produit |
| `Product_Title` | Texte court | Titre du produit |
| `Action` | Sélection | `REWRITE_COPY` / `SCALE_HERO` / `ARCHIVE` / `MONITOR` |
| `Reason` | Texte long | Explication de l'action déclenchée |
| `CVR_pct` | Nombre | CVR au moment de l'action |
| `Views_7d` | Nombre | Vues sur 7 jours |
| `Cart_adds_7d` | Nombre | Ajouts panier sur 7 jours |
| `Orders_7d` | Nombre | Commandes sur 7 jours |
| `Revenue_7d_CHF` | Devise | Revenu sur 7 jours |
| `Date` | Date-heure | Timestamp de l'action |
| `Applied` | Case à cocher | L'action a bien été appliquée |
| `Notes_Claude` | Texte long | Analyse de Claude qui a motivé l'action |

---

## Table 3 : `tblSuppliers` — Référentiel fournisseurs

| Champ | Type | Description |
|---|---|---|
| `Name` | Texte court | Nom du fournisseur / plateforme |
| `Source` | Sélection | `aliexpress` / `cj_dropshipping` / `spocket` / `zendrop` / `alibaba` |
| `Rating` | Nombre | Note moyenne (sur 5) |
| `Total_Orders_Fulfilled` | Nombre | Commandes remplies au total |
| `Avg_Shipping_Days_CH` | Nombre | Délai moyen vers la Suisse |
| `Avg_Shipping_Days_EU` | Nombre | Délai moyen vers l'EU |
| `Has_EU_Warehouse` | Case à cocher | Entrepôt en Europe |
| `Min_Order_Qty` | Nombre | MOQ (pour sourcing en volume) |
| `Notes` | Texte long | Remarques qualité, délais réels, etc. |
| `Active` | Case à cocher | Fournisseur actif dans le pipeline |

---

## Table 4 : `tblKPIs` — Tableau de bord KPIs hebdomadaire

| Champ | Type | Description |
|---|---|---|
| `Week` | Date | Semaine de référence |
| `Products_Active` | Nombre | Produits actifs en boutique |
| `Hero_Products` | Nombre | Produits identifiés "hero" |
| `Avg_CVR_pct` | Nombre | CVR moyen de la boutique |
| `AOV_CHF` | Devise | Panier moyen |
| `Revenue_CHF` | Devise | Revenu total de la semaine |
| `ROAS_Meta` | Nombre | ROAS Meta Ads |
| `ROAS_TikTok` | Nombre | ROAS TikTok Ads |
| `Products_Detected` | Nombre | Candidats détectés par Market Scout |
| `Products_Imported` | Nombre | Produits importés sur Shopify |
| `Products_Archived` | Nombre | Produits archivés |
| `Notes` | Texte long | Observations hebdo |

---

## Automatisations Airtable recommandées

1. **Alerte Slack/email** quand `Status = Importé — En attente validation`
   → Notifie John pour validation manuelle avant publication

2. **Alerte Slack/email** quand `Alerte_humaine = true`
   → Produit santé/médical à vérifier avant tout import

3. **Rapport hebdomadaire auto** (vendredi 17h)
   → Envoi d'un résumé des KPIs de la semaine par email

4. **Vue "Priorité cette semaine"** auto-générée
   → Sort par `Score DESC`, filtre `Status = Nouveau OR Rejeté` (pour réexamen)
