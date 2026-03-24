from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio

TOKEN = "8527771101:AAFr_5QJhwhJsJgbwoVUjzxaveyIizFnkVc"

players = []
game_active = False
registration_open = False
current_player_index = 0
waiting_end_turn = False
turn_task = None
coins = {}
stats = {}

truths = [
    "Який твій найбільший страх?",
    "Кого ти любиш найбільше (окрім родичів)?",
    "Який твій найбільший секрет?"
]

dares = [
    "Зміни нік на 10 хвилин",
    "Заспівай пісню",
    "Скинь фото"
]

# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, registration_open, current_player_index

    if registration_open or game_active:
        await update.message.reply_text("❌ Гра вже йде або реєстрація відкрита")
        return

    players = []
    game_active = False
    registration_open = True
    current_player_index = 0

    msg = await update.message.reply_text(
        "🔥 Реєстрація відкрита!\n\n"
        "Пиши /join щоб приєднатись\n"
        "⏳ Залишилося 60 секунд до початку гри"
    )

    context.application.create_task(
        registration_timer(context, update.effective_chat.id, msg.message_id)
    )


# --- TIMER REGISTRATION ---
async def registration_timer(context, chat_id, message_id):
    global registration_open, game_active

    for i in range(6):
        await asyncio.sleep(10)

        if not registration_open:
            return

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🔥 Реєстрація відкрита!\n\n"
                     f"Пиши /join щоб приєднатись\n"
                     f"⏳ Залишилося {60 - (i+1)*10} секунд до початку гри"
            )
        except:
            pass

    registration_open = False

    if len(players) < 2:
        await context.bot.send_message(chat_id, "❌ Недостатньо гравців")
        return

    game_active = True

    # 👉 додаємо ігри в статистику
    for p in players:
        if p not in stats:
            stats[p] = {"games": 0, "truth": 0, "dare": 0}
        stats[p]["games"] += 1

    await context.bot.send_message(chat_id, "🎮 Гра почалась!")

    await next_turn(context, chat_id)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not registration_open:
        return

    if len(players) >= 5:
        await update.message.reply_text("❌ Максимум 5 гравців")
        return

    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)

        if user.id not in coins:
            coins[user.id] = 20

        await update.message.reply_text(f"✅ {user.first_name} приєднався!")


# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    user = update.message.from_user

    if user.id not in players:
        return

    players.remove(user.id)

    await update.message.reply_text(
        f"❌ {user.first_name} вийшов\n👥 Гравців: {len(players)}"
    )

    if game_active and len(players) < 2:
        game_active = False
        await update.message.reply_text("⛔ Гру зупинено (мало гравців)")


# --- NEXT TURN ---
async def next_turn(context, chat_id):
    global current_player_index, waiting_end_turn, turn_task

    if not game_active or not players:
        return

    if current_player_index >= len(players):
        current_player_index = 0

    user = await context.bot.get_chat(players[current_player_index])
    name = user.first_name
    player_id = user.id

    keyboard = [["правда", "дія"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    waiting_end_turn = False

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎯 {name}, твій хід!\n\nОбери: правда або дія",
        reply_markup=reply_markup
    )

    if turn_task:
        turn_task.cancel()

    turn_task = context.application.create_task(
        turn_timer(context, chat_id, player_id)
    )


# --- TURN TIMER ---
async def turn_timer(context, chat_id, player_id):
    global current_player_index

    await asyncio.sleep(180)

    if not game_active:
        return

    if players[current_player_index] != player_id:
        return

    current_player_index += 1

    await context.bot.send_message(
        chat_id,
        "⏱ Час вийшов! Хід передано іншому гравцю"
    )

    await next_turn(context, chat_id)


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn, turn_task

    if not update.message or not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    if not waiting_end_turn:
        if text == "правда":
            if user.id not in stats:
                stats[user.id] = {"games": 0, "truth": 0, "dare": 0}

            stats[user.id]["truth"] += 1
            coins[user.id] += 5

            await update.message.reply_text(
                random.choice(truths),
                reply_markup=ReplyKeyboardRemove()
            )

        elif text == "дія":
            if user.id not in stats:
                stats[user.id] = {"games": 0, "truth": 0, "dare": 0}

            stats[user.id]["dare"] += 1
            coins[user.id] += 7

            await update.message.reply_text(
                random.choice(dares),
                reply_markup=ReplyKeyboardRemove()
            )

        else:
            return

        keyboard = [["завершити хід"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        waiting_end_turn = True

        await update.message.reply_text(
            "✅ Виконай завдання і натисни «завершити хід»",
            reply_markup=reply_markup
        )

    elif waiting_end_turn and text == "завершити хід":
        if turn_task:
            turn_task.cancel()

        current_player_index += 1
        waiting_end_turn = False

        await update.message.reply_text(
            "➡ Хід передано",
            reply_markup=ReplyKeyboardRemove()
        )

        await next_turn(context, update.effective_chat.id)


# --- MONEY ---
async def money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in coins:
        coins[user.id] = 0

    await update.message.reply_text(
        f"💎 У тебе {coins[user.id]} кристалів"
    )


# --- STATS ---
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in stats:
        stats[user.id] = {"games": 0, "truth": 0, "dare": 0}

    s = stats[user.id]

    await update.message.reply_text(
        f"📊 {user.first_name}\n\n"
        f"🎮 Ігор: {s['games']}\n"
        f"😇 Правда: {s['truth']}\n"
        f"😈 Дія: {s['dare']}"
    )


# --- TOP ---
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not stats:
        await update.message.reply_text("❌ Немає статистики")
        return

    text = "🏆 Топ гравців:\n\n"

    sorted_users = sorted(stats.items(), key=lambda x: x[1]["games"], reverse=True)

    for i, (user_id, s) in enumerate(sorted_users[:5], start=1):
        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name
        except:
            name = "Гравець"

        text += f"{i}. {name} — {s['games']} ігор\n"

    await update.message.reply_text(text)


# --- SKIP ---
async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index

    user = update.message.from_user

    if not game_active:
        return

    if user.id != players[current_player_index]:
        return

    if coins.get(user.id, 0) < 10:
        await update.message.reply_text("❌ Недостатньо кристалів (10)")
        return

    coins[user.id] -= 10
    current_player_index += 1

    await update.message.reply_text("⏭ Хід пропущено за 10 💎")

    await next_turn(context, update.effective_chat.id)


# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(CommandHandler("money", money))
app.add_handler(CommandHandler("skip", skip))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("top", top))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

app.run_polling()
