from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio

# 👉 ВСТАВ СЮДИ СВІЙ ТОКЕН
TOKEN = "8699261089:AAEd4BgScEn3bevDX6G650ZzGq6e7tZSp40"

players = []
game_active = False
current_player_index = 0
player_stats = {}

truths = ["Твій найбільший страх?", "Кого ти любиш?", "Твій секрет?"]
dares = ["Зміни нік на 10 хв", "Напиши 'я дивний'", "Скинь селфі"]


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, current_player_index, player_stats

    players = []
    player_stats = {}
    game_active = False
    current_player_index = 0

    await update.message.reply_text("🔥 Реєстрація відкрита! Пишіть /join (1 хв)")

    await asyncio.sleep(60)

    if len(players) < 2:
        await update.message.reply_text("❌ Недостатньо гравців")
        return

    game_active = True
    await update.message.reply_text("🎮 Гра почалась!")

    await next_turn(update, context)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        player_stats[user.id] = {"truth": 0, "dare": 0}
        await update.message.reply_text(f"✅ {user.first_name} приєднався!")

# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, game_active

    user = update.message.from_user

    if user.id in players:
        index = players.index(user.id)
        players.remove(user.id)
        player_stats.pop(user.id, None)

        await update.message.reply_text(f"❌ {user.first_name} вийшов")

        # якщо гравців менше 2 → стоп
        if len(players) < 2:
            game_active = False
            await update.message.reply_text("⛔ Гру зупинено (мало гравців)")
            return

        # якщо вийшов той хто ходив
        if index <= current_player_index:
            current_player_index -= 1


# --- NEXT TURN ---
async def next_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    if not game_active:
        return

    if not players:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Немає гравців"
        )
        return

    if current_player_index >= len(players):
        current_player_index = 0

    player_id = players[current_player_index]

    keyboard = [["правда", "дія"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<a href='tg://user?id={player_id}'>🎯 Твій хід!</a>\nОбери: правда або дія",
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

    if not players:
        return

    if user.id != players[current_player_index]:
        return

    stats = player_stats.get(user.id)
    if not stats:
        return

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
