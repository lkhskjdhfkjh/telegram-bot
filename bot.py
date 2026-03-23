from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("8699261089:AAHUKDhXNgUVkHNyOpkXHatlTRUZzM53n4U")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ПРИВІТ")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()
