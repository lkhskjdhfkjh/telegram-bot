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

truths = [
    "Який твій найбільший страх?",
    "Кого ти любиш?",
    "Твій секрет?"
]

dares = [
    "Зміни нік на 10 хв",
    "Напиши 'я дивний'",
    "Скинь селфі"
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
        "🔥 Реєстрація відкрита!\nПиши /join\n⏳ 60 секунд"
    )

    context.application.create_task(registration_timer(context, update.effective_chat.id, msg.message_id))


# --- TIMER ---
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
                text=f"🔥 Реєстрація відкрита!\nПиши /join\n⏳ {60 - (i+1)*10} сек"
            )
        except:
            pass

    registration_open = False

    if len(players) < 2:
        await context.bot.send_message(chat_id, "❌ Недостатньо гравців")
        return

    game_active = True
    await context.bot.send_message(chat_id, "🎮 Гра почалась!")

    await next_turn(context, chat_id)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not registration_open:
        await update.message.reply_text("❌ Зараз не можна приєднатись")
        return

    if len(players) >= 5:
        await update.message.reply_text("❌ Максимум 5 гравців")
        return

    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        await update.message.reply_text(f"✅ {user.first_name} приєднався!")


# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    user = update.message.from_user

    if user.id in players:
        players.remove(user.id)
        await update.message.reply_text(f"❌ {user.first_name} вийшов")

    if len(players) < 2:
        game_active = False
        await update.message.reply_text("⛔ Гру зупинено")


# --- NEXT TURN ---
async def next_turn(context, chat_id):
    global current_player_index, waiting_end_turn

    if not game_active or not players:
        return

    if current_player_index >= len(players):
        current_player_index = 0

    player_id = players[current_player_index]

    keyboard = [["правда", "дія"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    waiting_end_turn = False

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"<a href='tg://user?id={player_id}'>🎯 Твій хід!</a>\nОбери: правда або дія",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn

    if not update.message or not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    if not waiting_end_turn:
        if text == "правда":
            await update.message.reply_text(random.choice(truths))

        elif text == "дія":
            await update.message.reply_text(random.choice(dares))

        else:
            return

        keyboard = [["завершити хід"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        waiting_end_turn = True

        await update.message.reply_text(
            "👉 Натисни 'завершити хід'",
            reply_markup=reply_markup
        )

    elif waiting_end_turn and text == "завершити хід":
        current_player_index += 1
        waiting_end_turn = False

        await update.message.reply_text(
            "➡ Хід передано",
            reply_markup=ReplyKeyboardRemove()
        )

        await next_turn(context, update.effective_chat.id)


# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

app.run_polling()
