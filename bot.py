import os
import re
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BASE = Path(__file__).resolve().parent
ORIGINAL_FILENAME = "#Test-32 (Metal   Non Metal. ).html"
TEMPLATE = BASE / "template" / ORIGINAL_FILENAME
DEFAULT_NAME = "𝚳 𝐑 𝐒 𝐓 𝐑 𝚲 𝚴 𝐆 𝐄 𝐑 ™"
DEFAULT_LINK = "https://t.me/ENGLISH_BY_PRASHANT_SOLANKI_SIRR"

user_config = {}

def get_cfg(user_id):
    return user_config.setdefault(user_id, {"name": DEFAULT_NAME, "link": DEFAULT_LINK})

def valid_telegram_link(link: str) -> bool:
    return bool(re.fullmatch(r"https?://t\.me/[A-Za-z0-9_+\-/]+/?", link.strip()))

def build_html(name: str, link: str) -> str:
    html = TEMPLATE.read_text(encoding="utf-8")
    # Replace the template's current brand name.
    html = html.replace(DEFAULT_NAME, name)
    # Replace every occurrence of the template Telegram URL.
    html = html.replace(DEFAULT_LINK, link)
    return html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 HTML Name + Telegram Link Bot\n\n"
        "Commands:\n"
        "/setname Your Name\n"
        "/setlink https://t.me/your_channel\n"
        "/generate  → ready HTML file\n"
        "/show  → current name/link\n"
        "/reset  → default values\n\n"
        "Example:\n"
        "/setname 𝚳 𝐑 𝐒 𝐓 𝐑 𝚲 𝚴 𝐆 𝐄 𝐑 ™\n"
        "/setlink https://t.me/mychannel\n"
        "/generate"
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Example: /setname My Channel Name")
        return
    name = " ".join(context.args).strip()
    if len(name) > 120:
        await update.message.reply_text("❌ Name too long. Keep it under 120 characters.")
        return
    get_cfg(update.effective_user.id)["name"] = name
    await update.message.reply_text(f"✅ Name set to:\n{name}")

async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Example: /setlink https://t.me/mychannel")
        return
    link = context.args[0].strip()
    if not valid_telegram_link(link):
        await update.message.reply_text("❌ Valid Telegram link bhejo, e.g. https://t.me/mychannel")
        return
    get_cfg(update.effective_user.id)["link"] = link.rstrip("/")
    await update.message.reply_text(f"✅ Telegram link set to:\n{link.rstrip('/')}")

async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = get_cfg(update.effective_user.id)
    await update.message.reply_text(f"Current name:\n{cfg['name']}\n\nCurrent link:\n{cfg['link']}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_config[update.effective_user.id] = {"name": DEFAULT_NAME, "link": DEFAULT_LINK}
    await update.message.reply_text("♻️ Name aur link default par reset ho gaye.")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = get_cfg(update.effective_user.id)
    try:
        html = build_html(cfg["name"], cfg["link"])
        out = BASE / f"tmp_{update.effective_user.id}.html"
        out.write_text(html, encoding="utf-8")
        with out.open("rb") as f:
            await update.message.reply_document(
                document=f,
                filename=ORIGINAL_FILENAME,
                caption=ORIGINAL_FILENAME
            )
        out.unlink(missing_ok=True)
    except Exception as e:
        await update.message.reply_text(f"❌ Generate error: {type(e).__name__}: {e}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is missing")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setname", setname))
    app.add_handler(CommandHandler("setlink", setlink))
    app.add_handler(CommandHandler("show", show))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("generate", generate))
    print("Bot started")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
