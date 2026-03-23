from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio
import os

TOKEN = ("8699261089:AAEd4BgScEn3bevDX6G650ZzGq6e7tZSp40")  # для Railway

players = []
game_active = False
current_player_index = 0
player_stats = {}
lobby_message_id = None

truths = ["Твій найбільший страх?", "Кого ти любиш?", "Твій секрет?"]
dares = ["Зміни нік на 10 хв", "Напиши 'я дивний'", "Скинь селфі"]


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я працюю 😎 Напиши /startgame щоб почати гру")


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, current_player_index, player_stats, lobby_message_id

    players = []
    player_stats = {}
    game_active = False
    current_player_index = 0

    msg = await update.message.reply_text(
        "🔥 Реєстрація відкрита! Пишіть /join (1 хв)\n\nГравці:\n(поки нікого)"
    )

    lobby_message_id = msg.message_id

    await asyncio.sleep(60)

    if len(players) < 2:
        await update.message.reply_text("❌ Недостатньо гравців")
        return

    game_active = True
    await update.message.reply_text("🎮 Гра почалась!")

    await next_turn(update, context)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global lobby_message_id

    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        player_stats[user.id] = {"truth": 0, "dare": 0}

        # красиві імена
        player_names = []
        for p in players:
            member = await context.bot.get_chat_member(update.effective_chat.id, p)
            name = member.user.first_name
            player_names.append(f"• {name}")

        text = "🔥 Реєстрація відкрита! Пишіть /join (1 хв)\n\nГравці:\n"
        text += "\n".join(player_names)

        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=lobby_message_id,
                text=text
            )
        except:
            pass


# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, game_active

    user = update.message.from_user

    if user.id in players:
        index = players.index(user.id)
        players.remove(user.id)
        player_stats.pop(user.id, None)

        await update.message.reply_text(f"❌ {user.first_name} вийшов")

        if len(players) < 2:
            game_active = False
            await update.message.reply_text("⛔ Гру зупинено (мало гравців)")
            return

        if index <= current_player_index:
            current_player_index -= 1


# --- NEXT TURN ---
async def next_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    if not game_active or not players:
        return

    if current_player_index >= len(players):
        current_player_index = 0

    player_id = players[current_player_index]

    member = await context.bot.get_chat_member(update.effective_chat.id, player_id)
    name = member.user.first_name

    keyboard = [["правда", "дія"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎯 {name}, твій хід!\nОбери: правда або дія",
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


# --- APP ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

print("БОТ ЗАПУЩЕНИЙ 🔥")

app.run_polling()
