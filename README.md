# Bot Telegram Boutique de Services

## Description
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
