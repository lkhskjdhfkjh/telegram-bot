from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random

TOKEN = "8699261089:AAHUKDhXNgUVkHNyOpkXHatlTRUZzM53n4U"

players = []
game_active = False
current_player_index = 0
player_stats = {}

truths = [
    "Твій найбільший страх?",
    "Кого ти любиш?",
    "Твій секрет?",
    "Кого з чату ти ненавидиш?",
    "Кому б написав(ла) вночі?"
]

dares = [
    "Зміни нік на 10 хв",
    "Напиши 'я дивний'",
    "Скинь селфі",
    "Напиши будь-кому 'я люблю тебе'",
    "Скажи крінж фразу"
]


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пиши /startgame щоб почати 😈")


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, current_player_index, player_stats

    players = []
    player_stats = {}
    game_active = False
    current_player_index = 0

    await update.message.reply_text(
        "🔥 Реєстрація відкрита!\n/join — зайти\n/begin — почати"
    )


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        player_stats[user.id] = {"truth": 0, "dare": 0}
        await update.message.reply_text(f"{user.first_name} в грі 😎")


# --- BEGIN ---
async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    if len(players) < 2:
        await update.message.reply_text("❌ Треба мінімум 2 гравці")
        return

    game_active = True
    await update.message.reply_text("🎮 Гра почалась!")

    await next_turn(update, context)


# --- NEXT TURN ---
async def next_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    if not game_active:
        return

    if current_player_index >= len(players):
        current_player_index = 0

    player_id = players[current_player_index]

    keyboard = [["правда", "дія"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎯 Хід гравця {current_player_index + 1}\nОбери:",
        reply_markup=reply_markup
    )


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    if not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    stats = player_stats[user.id]

    if text == "правда":
        if stats["truth"] >= 3:
            await update.message.reply_text("❌ Забагато правди!")
            return

        stats["truth"] += 1
        stats["dare"] = 0
        await update.message.reply_text(random.choice(truths))

    elif text == "дія":
        if stats["dare"] >= 3:
            await update.message.reply_text("❌ Забагато дій!")
            return

        stats["dare"] += 1
        stats["truth"] = 0
        await update.message.reply_text(random.choice(dares))

    else:
        return

    current_player_index += 1
    await next_turn(update, context)


# --- APP ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("begin", begin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

print("БОТ ПРАЦЮЄ 🔥")

app.run_polling()
