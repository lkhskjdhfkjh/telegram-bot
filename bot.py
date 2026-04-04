import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# 🔑 ВСТАВ СВІЙ ТОКЕН
TOKEN = "8536774306:AAFf-SNStloCvTiHa15ksYyTdRlQhae0NFg"

# 👑 АДМІНИ
OWNER_ID = 7801504329
COOWNER_ID = 6362536798
ADMINS = [OWNER_ID, COOWNER_ID]

# 💾 БАЗА ДАНИХ
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

# 🔄 СТАНИ ДІАЛОГУ
AGE, NAME, REASON, SKILLS, ORDER = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # перевірка чи є в базі
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
    db_user = cursor.fetchone()

    # якщо нема профілю
    if not db_user:
        if user.id in ADMINS:
            rank = "Власник" if user.id == OWNER_ID else "Співвласник"

            cursor.execute("""
            INSERT INTO users (user_id, username, name, rank, approved)
            VALUES (?, ?, ?, ?, 1)
            """, (user.id, user.username, "Адмін", rank))
            conn.commit()
        else:
            keyboard = [["⚔️ Стати рейдером", "💣 Замовити рейд"]]

            await update.message.reply_text(
                "👋 Привіт.\n\n"
                "Ти потрапив у систему VOID.\n"
                "Тут ти можеш:\n"
                "• приєднатися до рейдерів\n"
                "• або замовити рейд\n\n"
                "Обери потрібну дію нижче:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return

    # якщо адмін
    if user.id in ADMINS:
        await update.message.reply_text("🔧 Адмін режим активовано.")
        await profile(update, context)
        return

    # звичайний користувач
    await profile(update, context)
    async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "⚔️ Стати рейдером":
        await update.message.reply_text(
            "📋 Починаємо анкету.\n\n"
            "Вкажи свій вік:"
        )
        return AGE

    elif text == "💣 Замовити рейд":
        await update.message.reply_text(
            "🔗 Надішли посилання на ціль.\n\n"
            "Я передам його адміністрації після перевірки."
        )
        return ORDER
        async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text

    await update.message.reply_text(
        "✏️ Добре.\n\n"
        "Тепер напиши своє ім'я або псевдонім:"
    )
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "❓ Чому ти вирішив(ла) стати рейдером?\n\n"
        "Опиши коротко свою мотивацію:"
    )
    return REASON


async def reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reason"] = update.message.text

    await update.message.reply_text(
        "🧠 Останнє питання.\n\n"
        "Які в тебе навички?\n"
        "(досвід, що вмієш, що робив раніше)"
    )
    return SKILLS
    async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["skills"] = update.message.text

    # зберігаємо в базу
    cursor.execute("""
    # перевірка чи вже є анкета
cursor.execute("SELECT approved FROM users WHERE user_id=?", (user.id,))
existing = cursor.fetchone()

if existing and existing[0] == 0:
    await update.message.reply_text(
        "⏳ Ти вже відправляв анкету.\n"
        "Очікуй рішення адміністрації."
    )
    return ConversationHandler.END (user_id, username, name, age, reason, skills)
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

    # текст анкети
    text = f"""📥 НОВА АНКЕТА

👤 @{user.username}
🆔 {user.id}

Ім'я: {context.user_data["name"]}
Вік: {context.user_data["age"]}
Причина: {context.user_data["reason"]}
Скіли: {context.user_data["skills"]}
"""

    # кнопки
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{user.id}")]
    ])

    # відправка адмінам
    for admin in ADMINS:
        await context.bot.send_message(admin, text, reply_markup=keyboard)

    # відповідь користувачу
    await update.message.reply_text(
        "✅ Я відправив твою анкету адміністрації.\n\n"
        "⏳ Очікуй рішення. З тобою зв'яжуться після перевірки."
    )

    return ConversationHandler.END

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    link = update.message.text.strip()

    # перевірка посилання
    if not (link.startswith("http://") or link.startswith("https://")):
        await update.message.reply_text(
            "❌ Це не схоже на посилання.\n\n"
            "Надішли коректний лінк (наприклад: https://t.me/...)."
        )
        return ORDER

    # текст для адмінів
    text = f"""💣 НОВЕ ЗАМОВЛЕННЯ

👤 @{user.username}
🆔 {user.id}

🔗 {link}
"""

    # відправка адмінам
    for admin in ADMINS:
        await context.bot.send_message(admin, text)

    # відповідь користувачу
    await update.message.reply_text(
        "✅ Я відправив твоє замовлення адміністрації.\n\n"
        "⏳ Очікуй відповідь. Якщо замовлення приймуть — з тобою зв'яжуться."
    )

    return ConversationHandler.END
    async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[1])

    # тільки адміни можуть натискати
    if query.from_user.id not in ADMINS:
        return

    # прийняти
    if "approve" in data:
        cursor.execute("UPDATE users SET approved=1 WHERE user_id=?", (user_id,))
        conn.commit()

        await context.bot.send_message(
            user_id,
            "🎉 Вітаю.\n\n"
            "Тебе прийнято в систему VOID.\n"
            "Найближчим часом тобі можуть видати наставника."
        )

        await query.edit_message_text("✅ Користувача прийнято")

    # відхилити
    elif "reject" in data:
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()

        await context.bot.send_message(
            user_id,
            "❌ На жаль, твою анкету відхилено.\n\n"
            "Можеш спробувати ще раз пізніше."
        )

        await query.edit_message_text("❌ Користувача відхилено")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        await update.message.reply_text(
            "❌ Профіль не знайдено.\n\n"
            "Спробуй написати /start"
        )
        return

    status = "✅ Прийнятий" if user[8] == 1 else "⏳ На розгляді"

    text = f"""👤 ПРОФІЛЬ

Ім'я: {user[2]}
Ранг: {user[6]}
Рейди: {user[7]}

Статус: {status}
"""

    await update.message.reply_text(text)
