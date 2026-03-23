from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import os
import asyncio

TOKEN = os.getenv("TOKEN")

players = []
game_active = False
current_player_index = 0
player_stats = {}

truths = ["Твій найбільший страх?", "Кого ти любиш?", "Твій секрет?"]
dares = ["Зміни нік на 10 хв", "Напиши 'я дивний'", "Скинь селфі"]


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, current_player_index

    players = []
    game_active = False
    current_player_index = 0

    await update.message.reply_text("Реєстрація відкрита! Пишіть /join (1 хвилина)")

    await asyncio.sleep(60)

    if len(players) < 2:
        await update.message.reply_text("Недостатньо гравців 😢")
        return

    game_active = True
    await update.message.reply_text("Гра почалась 🔥")

    await next_turn(update, context)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        player_stats[user.id] = {"truth": 0, "dare": 0}
        await update.message.reply_text(f"{user.first_name} приєднався!")


# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id in players:
        players.remove(user.id)
        await update.message.reply_text(f"{user.first_name} вийшов з гри")


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
        text=f"<a href='tg://user?id={player_id}'>Твій хід!</a>\nОбери: правда або дія",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    if not update.message:
        return

    if not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    stats = player_stats[user.id]

    if text == "правда":
        if stats["truth"] >= 3:
            await update.message.reply_text("❌ Забагато правди! Обери дію 😈")
            return

        stats["truth"] += 1
        stats["dare"] = 0

        await update.message.reply_text(random.choice(truths))

    elif text == "дія":
        if stats["dare"] >= 3:
            await update.message.reply_text("❌ Забагато дій! Обери правду 😈")
            return

        stats["dare"] += 1
        stats["truth"] = 0

        await update.message.reply_text(random.choice(dares))

    else:
        return

    current_player_index += 1
    await next_turn(update, context)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

app.run_polling()
