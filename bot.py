import os
import re
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

# Dummy HTTP server taaki Railway Web Service Crash na ho
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    server.serve_forever()

# User Settings
user_config = {}

def get_config(user_id):
    return user_config.setdefault(user_id, {
        "name": None,
        "link": None,
        "html_path": None,
        "filename": None,
    })

def replace_html(html, name=None, link=None):
    if name:
        patterns = [
            r'(Lαɳɳιʂƚҽɾ ꝈօվąӀ)',
            r'(𝚳\s*𝐑\s*𝐒\s*𝐓\s*𝐑\s*𝚲\s*𝚴\s*𝐆\s*𝐄\s*𝐑\s*™)',
        ]
        for p in patterns:
            html = re.sub(p, name, html)

        html = re.sub(
            r'(<title>\s*)[^<]*(\s*</title>)',
            lambda m: m.group(1) + name + m.group(2),
            html,
            count=1,
            flags=re.I,
        )

    if link:
        html = re.sub(r'https://t\.me/[A-Za-z0-9_+/?=-]+', link, html)

    return html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "HTML Editor Bot ready ✅\n\n"
        "1. HTML file upload karo.\n"
        "2. /setname Your Name\n"
        "3. /setlink https://t.me/yourchannel\n"
        "4. /generate\n\n"
        "Commands:\n"
        "/start - Help\n"
        "/setname - Name set karo\n"
        "/setlink - Telegram link set karo\n"
        "/generate - Edited HTML bhejo\n"
        "/show - Current settings\n"
        "/reset - Settings reset"
    )

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = " ".join(context.args).strip()
    if not value:
        await update.message.reply_text("Use: /setname Your Name")
        return
    get_config(update.effective_user.id)["name"] = value
    await update.message.reply_text(f"Name set ✅\n{value}")

async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = " ".join(context.args).strip()
    if not re.match(r'^https://t\.me/[A-Za-z0-9_+/?=-]+$', value):
        await update.message.reply_text("Valid Telegram link do.\nExample: /setlink https://t.me/yourchannel")
        return
    get_config(update.effective_user.id)["link"] = value
    await update.message.reply_text(f"Telegram link set ✅\n{value}")

async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = get_config(update.effective_user.id)
    await update.message.reply_text(
        f"Name: {c['name'] or 'Not set'}\n"
        f"Link: {c['link'] or 'Not set'}\n"
        f"HTML: {c['filename'] or 'Not uploaded'}"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_config.pop(update.effective_user.id, None)
    await update.message.reply_text("Settings reset ✅")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith((".html", ".htm")):
        await update.message.reply_text("Sirf .html ya .htm file upload karo.")
        return

    tg_file = await context.bot.get_file(doc.file_id)
    workdir = Path(tempfile.gettempdir()) / f"htmlbot_{update.effective_user.id}"
    workdir.mkdir(parents=True, exist_ok=True)
    path = workdir / Path(doc.file_name).name
    await tg_file.download_to_drive(custom_path=str(path))

    c = get_config(update.effective_user.id)
    c["html_path"] = str(path)
    c["filename"] = doc.file_name

    await update.message.reply_text(
        f"HTML received ✅\nFile: {doc.file_name}\n\n"
        "Ab /setname aur /setlink use karo, phir /generate."
    )

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = get_config(update.effective_user.id)

    if not c["html_path"] or not Path(c["html_path"]).exists():
        await update.message.reply_text("Pehle HTML file upload karo.")
        return

    if not c["name"] and not c["link"]:
        await update.message.reply_text("Pehle /setname aur/or /setlink set karo.")
        return

    src = Path(c["html_path"])
    try:
        html = src.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        html = src.read_text(encoding="utf-8-sig")

    edited = replace_html(html, c["name"], c["link"])

    out = src.parent / f"edited_{src.name}"
    out.write_text(edited, encoding="utf-8")

    with out.open("rb") as f:
        await update.message.reply_document(
            document=f,
            filename=c["filename"],
            caption=c["filename"],
        )

# Main block ko synchronous rakha gaya hai taaki event loop crash bilkul na ho
def main():
    # Railway health check pass karne ke liye built-in HTTP server
    threading.Thread(target=run_http_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setname", setname))
    app.add_handler(CommandHandler("setlink", setlink))
    app.add_handler(CommandHandler("show", show))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
