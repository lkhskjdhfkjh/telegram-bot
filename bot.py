from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8699261089:AAEd4BgScEn3bevDX6G650ZzGq6e7tZSp40"

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/start":
        await update.message.reply_text("Пока")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, reply))

app.run_polling()