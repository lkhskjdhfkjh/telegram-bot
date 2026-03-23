from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random

TOKEN = "8699261089:AAEd4BgScEn3bevDX6G650ZzGq6e7tZSp40"

players = []
game_active = False
current_player_index = 0
player_stats = {}
registration_open = False

truths = [
    "Твій найбільший страх?",
    "Кого ти любиш?",
    "Твій секрет?"
]

dares = [
    "Зміни нік на 10 хв",
    "Напиши 'я дивний'",
    "Скинь селфі"
]


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я працюю 😎 /startgame щоб почати гру")


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, current_player_index, player_stats, registration_open

    players = []
    player_stats = {}
    game_active = False
    current_player_index = 0
    registration_open = True

    await update.message.reply_text(
        "🔥 Реєстрація відкрита!\nНапишіть /join\n\nКоли всі зайдуть → напишіть /begin"
    )


# --- BEGIN GAME (ручний старт) ---
async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active, registration_open

    if len(players) < 2:
        await update.message.reply_text("❌ Треба мінімум 2 гравці")
        return

    registration_open = False
    game_active = True

    await update.message.reply_text("🎮 Гра почалась!")

    await next_turn(update, context)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players

    if not registration_open:
        return

    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        player_stats[user.id] = {"truth": 0, "dare": 0}

        await update.message.reply_text(f"{user.first_name} приєднався!")


# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, game_active

    user = update.message.from_user

    if user.id in players:
        index = players.index(user.id)
        players.remove(user.id)
        player_stats.pop(user.id, None)

        await update.message.reply_text(f"{user.first_name} вийшов")

        if len(players) < 2:
            game_active = False
            await update.message.reply_text("⛔ Гру зупинено")
            return

        if index <= current_player_index:
            current_player_index -= 1


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
        text=f"🎯 Гравець {current_player_index + 1}, твій хід!",
        reply_markup=reply_markup
    )


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    if not update.message or not game_active:
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
app.add_handler(CommandHandler("begin", begin))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

print("БОТ ПРАЦЮЄ 🔥")

app.run_polling()
