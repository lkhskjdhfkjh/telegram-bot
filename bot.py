import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

TOKEN = "8536774306:AAFf-SNStloCvTiHa15ksYyTdRlQhae0NFg"

OWNER_ID = 7801504329
COOWNER_ID = 6362536798
ADMIN_ID = 7295595580

# ===== БАЗА =====
conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    age TEXT,
    reason TEXT,
    skills TEXT,
    rank TEXT DEFAULT 'Новачок',
    raids INTEGER DEFAULT 0,
    approved INTEGER DEFAULT 0
)
""")
conn.commit()

# ===== СТАНИ =====
AGE, NAME, REASON, SKILLS, ORDER = range(5)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in [OWNER_ID, COOWNER_ID]:
        await update.message.reply_text("Адмін режим")
        return

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user:
        await profile(update, context)
    else:
        keyboard = [["Стати рейдером", "Замовити рейд"]]
        await update.message.reply_text(
            "VOID.EXE",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

# ===== ВИБІР =====
async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Стати рейдером":
        await update.message.reply_text("Вік:")
        return AGE

    elif text == "Замовити рейд":
        await update.message.reply_text("Скинь посилання:")
        return ORDER

# ===== АНКЕТА =====
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Ім'я:")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Чому хочеш стати рейдером?")
    return REASON

async def reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reason"] = update.message.text
    await update.message.reply_text("Скіли:")
    return SKILLS

async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["skills"] = update.message.text

    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, username, name, age, reason, skills)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username,
        context.user_data["name"],
        context.user_data["age"],
        context.user_data["reason"],
        context.user_data["skills"]
    ))
    conn.commit()

    text = f"""АНКЕТА

@{user.username}
ID: {user.id}

Ім'я: {context.user_data["name"]}
Вік: {context.user_data["age"]}
Причина: {context.user_data["reason"]}
Скіли: {context.user_data["skills"]}
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{user.id}")]
    ])

    await context.bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
    await update.message.reply_text("Анкета відправлена")

    return ConversationHandler.END

# ===== ЗАМОВЛЕННЯ =====
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    link = update.message.text

    text = f"""НОВЕ ЗАМОВЛЕННЯ

@{user.username}
ID: {user.id}

Посилання:
{link}
"""

    await context.bot.send_message(OWNER_ID, text)
    await context.bot.send_message(COOWNER_ID, text)

    await update.message.reply_text("Замовлення відправлено")

    return ConversationHandler.END

# ===== КНОПКИ =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[1])

    if query.from_user.id not in [OWNER_ID, COOWNER_ID]:
        return

    if "approve" in data:
        cursor.execute("UPDATE users SET approved=1 WHERE user_id=?", (user_id,))
        conn.commit()
        await context.bot.send_message(user_id, "Тебе прийнято")
        await query.edit_message_text("Прийнято")

    elif "reject" in data:
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()
        await context.bot.send_message(user_id, "Тебе відхилено")
        await query.edit_message_text("Відхилено")

# ===== ПРОФІЛЬ =====
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        await update.message.reply_text("Нема профілю")
        return

    text = f"""ПРОФІЛЬ

Ім'я: {user[2]}
Ранг: {user[6]}
Рейди: {user[7]}
"""

    await update.message.reply_text(text)

# ===== ЗАПУСК =====
app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, choose)],
    states={
        AGE: [MessageHandler(filters.TEXT, age)],
        NAME: [MessageHandler(filters.TEXT, name)],
        REASON: [MessageHandler(filters.TEXT, reason)],
        SKILLS: [MessageHandler(filters.TEXT, skills)],
        ORDER: [MessageHandler(filters.TEXT, order)],
    },
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(conv)
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
