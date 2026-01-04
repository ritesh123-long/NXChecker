import os
import re
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

app = Flask(__name__)

# ---------- Instagram Check ----------
def check_instagram(username: str):
    username = username.strip().lower()

    if username.startswith("@"):
        username = username[1:]

    if not re.match(r"^[a-z0-9._]+$", username):
        return {"valid": False, "reason": "invalid_chars"}

    url = f"https://www.instagram.com/{username}/"

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        if res.status_code == 200:
            is_private = '"is_private":true' in res.text
            return {"valid": True, "exists": True, "private": is_private, "url": url}

        elif res.status_code == 404:
            return {"valid": True, "exists": False}

        else:
            return {"valid": True, "exists": None}

    except Exception:
        return {"valid": True, "exists": None}


# ---------- Telegram Bot ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send an Instagram username to check.\n"
        "Example: cristiano / @virat.kohli"
    )

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /check username")
    await handle_username(update, context.args[0])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_username(update, update.message.text)

async def handle_username(update, username):
    msg = await update.message.reply_text("⏳ Checking…")
    result = check_instagram(username)

    if not result["valid"]:
        return await msg.edit_text("⚠️ Invalid username format.")

    if result["exists"] is True:
        status = "🔒 Private" if result["private"] else "🌍 Public"
        await msg.edit_text(
            f"✅ Account Found\n👤 {username}\n{status}\n🔗 {result['url']}"
        )
    elif result["exists"] is False:
        await msg.edit_text("❌ Account Not Found")
    else:
        await msg.edit_text("⚠️ Could not verify (rate-limit / network)")


def run_bot():
    app_tg = ApplicationBuilder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("check", check_cmd))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling()


# ---------- Render Health Endpoint ----------
@app.get("/")
def health():
    return "OK — Telegram bot running"


# ---------- Main ----------
if __name__ == "__main__":
    # Bot runs in background thread
    threading.Thread(target=run_bot, daemon=True).start()

    # Flask listens on Render PORT
    app.run(host="0.0.0.0", port=PORT)
