import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

WAITING_FILE, WAITING_NAME, WAITING_LINK = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Kripya apni HTML file bhejain jise edit karna hai.")
    return WAITING_FILE

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    
    if not document.file_name.endswith('.html'):
        await update.message.reply_text("Kripya sirf valid .html file hi bhejein.")
        return WAITING_FILE

    file = await document.get_file()
    file_path = f"temp_{document.file_name}"
    await file.download_to_drive(file_path)

    context.user_data['file_path'] = file_path
    context.user_data['original_filename'] = document.file_name

    await update.message.reply_text("File mil gayi! Ab bataiye aapko konsa **Owner/Brand Name** replace karna hai?")
    return WAITING_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_name'] = update.message.text
    await update.message.reply_text("Name save ho gaya! Ab bataiye konsa **Link** replace karna hai?")
    return WAITING_LINK

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_link = update.message.text
    new_name = context.user_data['new_name']
    file_path = context.user_data['file_path']
    original_filename = context.user_data['original_filename']

    await update.message.reply_text("File process ho rahi hai, kripya thoda wait karein...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Dynamic Replace Logic
        modified_content = content.replace("🔥 Custom Brand Name 🔥", new_name)
        modified_content = modified_content.replace("https://t.me/YourTelegramChannelLink", new_link)
        modified_content = modified_content.replace("{{OWNER_TAG}}", new_name)
        modified_content = modified_content.replace("{{JOIN_CHANNEL_LINK}}", new_link)

        output_filename = f"updated_{original_filename}"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        with open(output_filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                caption="✅ Aapki modified HTML file ready hai!"
            )

        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_filename):
            os.remove(output_filename)

    except Exception as e:
        await update.message.reply_text(f"File process karne me error aaya: {str(e)}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Process cancel kar diya gaya hai.")
    return ConversationHandler.END

if __name__ == '__main__':
    # Token Environment Variable se automatic load hoga
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN Environment Variable nahi mila!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                WAITING_FILE: [MessageHandler(filters.Document.ALL, handle_document)],
                WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
                WAITING_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        app.add_handler(conv_handler)
        print("Bot running...")
        app.run_polling()
        
