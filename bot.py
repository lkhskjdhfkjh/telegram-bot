import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

TOKEN = "8536774306:AAFf-SNStloCvTiHa15ksYyTdRlQhae0NFg"

OWNER_ID = 7801504329
COOWNER_ID = 6362536798
ADMINS = [OWNER_ID, COOWNER_ID]

# ===== БАЗА =====
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

AGE, NAME, REASON, SKILLS, ORDER, DELETE = range(6)

# ===== СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Реєстрація", callback_data="reg")],
        [InlineKeyboardButton("💣 Замовити рейд", callback_data="order")]
    ])

    await update.message.reply_text(
        "👋 Привіт.\n\nОбери дію:",
        reply_markup=keyboard
    )

# ===== МЕНЮ =====
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # перевірка реєстрації
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() and query.data == "reg":
        await query.message.reply_text("⚠️ Ти вже зареєстрований")
        return ConversationHandler.END

    if query.data == "reg":
        await query.message.reply_text("📋 Вкажи свій вік:")
        return AGE

    elif query.data == "order":
        await query.message.reply_text("🔗 Надішли посилання:")
        return ORDER

# ===== АНКЕТА =====
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Ім'я або нік:")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Чому хочеш вступити?")
    return REASON

async def reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reason"] = update.message.text
    await update.message.reply_text("Твої навички:")
    return SKILLS

async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["skills"] = update.message.text

    text = f"""📥 АНКЕТА

👤 @{user.username}
🆔 {user.id}

Ім'я: {context.user_data["name"]}
Вік: {context.user_data["age"]}
Причина: {context.user_data["reason"]}
Скіли: {context.user_data["skills"]}
"""

    await context.bot.send_message(OWNER_ID, text)

    # зберігаємо юзера
    cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user.id,))
    conn.commit()

    await update.message.reply_text("✅ Я відправив анкету")

    return ConversationHandler.END

# ===== ЗАМОВЛЕННЯ =====
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    link = update.message.text

    if not link.startswith("http"):
        await update.message.reply_text("❌ Це не посилання")
        return ORDER

    text = f"""💣 НОВЕ ЗАМОВЛЕННЯ

👤 @{user.username}
🆔 {user.id}

🔗 {link}
"""

    await context.bot.send_message(OWNER_ID, text)

    await update.message.reply_text("✅ Я відправив замовлення")

    return ConversationHandler.END

# ===== ПАНЕЛЬ =====
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ Нема доступу")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Список", callback_data="list")],
        [InlineKeyboardButton("🗑 Видалити", callback_data="delete")]
    ])

    await update.message.reply_text("🔧 Панель:", reply_markup=keyboard)

# ===== КНОПКИ ПАНЕЛІ =====
async def panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMINS:
        return

    if query.data == "list":
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        text = "📊 СПИСОК:\n\n"

        for u in users:
            try:
                chat = await context.bot.get_chat(u[0])
                name = chat.first_name
                username = f"@{chat.username}" if chat.username else "без юзера"

                text += f"👤 {name}\n{username}\n🆔 {u[0]}\n\n"
            except:
                text += f"🆔 {u[0]}\n\n"

        await query.message.reply_text(text)

    elif query.data == "delete":
        await query.message.reply_text("✏️ Введи ID:")
        return DELETE

# ===== ВИДАЛЕННЯ =====
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    try:
        uid = int(update.message.text)
        cursor.execute("DELETE FROM users WHERE user_id=?", (uid,))
        conn.commit()
        await update.message.reply_text("✅ Видалено")
    except:
        await update.message.reply_text("❌ Помилка")

    return ConversationHandler.END

# ===== ЗАПУСК =====
app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu)],
    states={
        AGE: [MessageHandler(filters.TEXT, age)],
        NAME: [MessageHandler(filters.TEXT, name)],
        REASON: [MessageHandler(filters.TEXT, reason)],
        SKILLS: [MessageHandler(filters.TEXT, skills)],
        ORDER: [MessageHandler(filters.TEXT, order)],
        DELETE: [MessageHandler(filters.TEXT, delete_user)],
    },
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(conv)
app.add_handler(CallbackQueryHandler(panel_buttons))

print("Бот працює 🚀")

app.run_polling()
