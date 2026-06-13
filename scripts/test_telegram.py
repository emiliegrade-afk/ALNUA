"""Test rapide Telegram — envoie un message de test depuis le Hub."""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant dans .env")
        return

    from telegram import Bot
    bot = Bot(token=token)

    msg = (
        "🤖 ALNUA Hub — Test Telegram\n\n"
        "✅ La connexion fonctionne !\n"
        "Le Hub peut t'envoyer des notifications pour :\n"
        "• 🔧 Bugs détectés et corrigés automatiquement\n"
        "• 💡 Rapport hebdomadaire R&D\n"
        "• 📊 Briefing matinal agents"
    )

    await bot.send_message(chat_id=int(chat_id), text=msg)
    print("✅ Message envoyé sur Telegram !")

asyncio.run(main())
