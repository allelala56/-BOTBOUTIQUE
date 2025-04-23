import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Récupération du token et des variables depuis l'environnement
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "blackdjdj")
SOLANA_ADDRESS = os.getenv("SOLANA_ADDRESS", "DVaoLjuk8qsc3KbM84JoCHNSFLuVpwtLsD6ac6jWuzWx")

if not BOT_TOKEN:
    raise RuntimeError("Le token BOT_TOKEN n'est pas défini dans les variables d'environnement.")

bot = telebot.TeleBot(BOT_TOKEN)

# Clavier principal
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(KeyboardButton("Spam sur lien : 25€ / 1k"))
menu_keyboard.add(KeyboardButton("Technique Pristelle : 50€"))
menu_keyboard.add(KeyboardButton("Logs (Facebook, Amazon, Netflix, Mobiax) : 10€ par log"))
menu_keyboard.add(KeyboardButton("💬 Support"))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user.first_name or "utilisateur"
    text = f"Bonjour {user} !
Bienvenue sur notre bot de services.
Choisissez un service :"
    bot.send_message(message.chat.id, text, reply_markup=menu_keyboard)

@bot.message_handler(func=lambda m: m.text and "spam sur lien" in m.text.lower())
def service_spam(message):
    text = (
        "<b>📌 Service : Spam sur lien</b>
"
        "➡️ Prix : 25€ pour 1000 envois
"
        f"💰 Paiement (Solana) : <code>{SOLANA_ADDRESS}</code>

"
        "Envoyez la preuve de paiement pour finaliser."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and "technique pristelle" in m.text.lower())
def service_pristelle(message):
    text = (
        "<b>📌 Service : Technique Pristelle</b>
"
        "➡️ Prix : 50€ (3 SIM par compte, remboursable)
"
        f"💰 Paiement (Solana) : <code>{SOLANA_ADDRESS}</code>

"
        "Après paiement, vous recevrez la méthode complète."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and "logs" in m.text.lower())
def service_logs(message):
    text = (
        "<b>📌 Service : Logs</b>
"
        "➡️ Prix : 10€ par log (Facebook, Amazon, Netflix, Mobiax)
"
        f"💰 Paiement (Solana) : <code>{SOLANA_ADDRESS}</code>

"
        "Envoyez la preuve de paiement pour recevoir les infos."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and "support" in m.text.lower())
def support(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Contacter le support", url=f"https://t.me/{SUPPORT_USERNAME}"))
    bot.send_message(message.chat.id, "Cliquez ci-dessous pour contacter le support :", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "Commande non reconnue. Utilisez le menu.", reply_markup=menu_keyboard)

bot.infinity_polling()
