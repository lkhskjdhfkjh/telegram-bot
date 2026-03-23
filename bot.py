from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio
import json

TOKEN = "8527771101:AAFr_5QJhwhJsJgbwoVUjzxaveyIizFnkVc"

players = []
game_active = False
registration_open = False
current_player_index = 0
waiting_end_turn = False

global_stats = {}
STATS_FILE = "stats.json"


truths = ["Твій страх?", "Кого любиш?", "Твій секрет?"]
dares = ["Зміни нік", "Напиши крінж", "Скинь селфі"]


# --- SAVE / LOAD ---
def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(global_stats, f)


def load_stats():
    global global_stats
    try:
        with open(STATS_FILE, "r") as f:
            global_stats = json.load(f)
    except:
        global_stats = {}


# --- LEVEL ---
def get_level(total):
    if total < 10:
        return "😐 Новачок"
    elif total < 30:
        return "😎 Норм"
    elif total < 60:
        return "🔥 Про"
    else:
        return "👑 Бог"


# --- INIT USER ---
def init_user(chat_id, user_id):
    chat_id = str(chat_id)
    user_id = str(user_id)

    if chat_id not in global_stats:
        global_stats[chat_id] = {}

    if user_id not in global_stats[chat_id]:
        global_stats[chat_id][user_id] = {
            "games": 0,
            "truth": 0,
            "dare": 0
        }


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пиши /startgame 😈")


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, registration_open, current_player_index

    players = []
    game_active = False
    registration_open = True
    current_player_index = 0

    chat_id = update.effective_chat.id

    msg = await update.message.reply_text(
        "🔥 РЕЄСТРАЦІЯ В ГРУ ВІДКРИТА\n\n"
        "⏳ Час: 60 секунд\n"
        "👥 Максимум: 5 гравців\n\n"
        "👉 Напиши /join щоб зайти\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🎮 ГРАВЦІ:\n"
        "поки нікого 😢\n"
        "━━━━━━━━━━━━━━━"
    )

    try:
        await context.bot.pin_chat_message(chat_id, msg.message_id)
    except:
        pass

    for i in range(6):
        await asyncio.sleep(10)

        if not registration_open:
            return

        names = []
        for p in players:
            try:
                member = await context.bot.get_chat_member(chat_id, p)
                names.append(f"• {member.user.first_name}")
            except:
                names.append("• ???")

        player_list = "\n".join(names) if names else "поки нікого 😢"

        text = (
            "🔥 РЕЄСТРАЦІЯ В ГРУ ВІДКРИТА\n\n"
            f"⏳ Залишилось: {60 - (i+1)*10} сек\n"
            "👥 Максимум: 5 гравців\n\n"
            "👉 Напиши /join щоб зайти\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🎮 ГРАВЦІ:\n"
            f"{player_list}\n"
            "━━━━━━━━━━━━━━━"
        )

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text=text
            )
        except:
            pass

    registration_open = False

    if len(players) < 2:
        await context.bot.send_message(chat_id, "❌ Недостатньо гравців")
        return

    await context.bot.send_message(chat_id, "🎮 ГРА ПОЧАЛАСЬ!")
    await begin_game(update, context)


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not registration_open:
        await update.message.reply_text("❌ Реєстрація закрита")
        return

    if len(players) >= 5:
        await update.message.reply_text("❌ Макс 5 гравців")
        return

    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        await update.message.reply_text(f"{user.first_name} в грі 😎")


# --- LEAVE ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, game_active

    user = update.message.from_user

    if user.id in players:
        index = players.index(user.id)
        players.remove(user.id)

        await update.message.reply_text(f"{user.first_name} вийшов")

        if len(players) < 2:
            game_active = False
            await update.message.reply_text("⛔ Гру завершено")
            return

        if index <= current_player_index:
            current_player_index -= 1


# --- BEGIN GAME ---
async def begin_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    game_active = True
    chat_id = str(update.effective_chat.id)

    for p in players:
        init_user(chat_id, p)
        global_stats[chat_id][str(p)]["games"] += 1

    save_stats()

    await next_turn(update, context)


# --- NEXT TURN ---
async def next_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn

    if current_player_index >= len(players):
        current_player_index = 0

    player_id = players[current_player_index]
    member = await context.bot.get_chat_member(update.effective_chat.id, player_id)

    waiting_end_turn = False

    keyboard = [["правда", "дія"]]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎯 {member.user.first_name}, твій хід",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn

    if not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()
    chat_id = str(update.effective_chat.id)

    if user.id != players[current_player_index]:
        return

    init_user(chat_id, user.id)

    if waiting_end_turn:
        if text == "завершити хід":
            await update.message.reply_text("Хід завершено", reply_markup=ReplyKeyboardRemove())
            current_player_index += 1
            await next_turn(update, context)
        return

    if text == "правда":
        global_stats[chat_id][str(user.id)]["truth"] += 1
        save_stats()

        await update.message.reply_text(
            random.choice(truths),
            reply_markup=ReplyKeyboardMarkup([["завершити хід"]], resize_keyboard=True)
        )

        waiting_end_turn = True

    elif text == "дія":
        global_stats[chat_id][str(user.id)]["dare"] += 1
        save_stats()

        await update.message.reply_text(
            random.choice(dares),
            reply_markup=ReplyKeyboardMarkup([["завершити хід"]], resize_keyboard=True)
        )

        waiting_end_turn = True


# --- STATS ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = str(update.effective_chat.id)

    init_user(chat_id, user.id)

    s = global_stats[chat_id][str(user.id)]
    total = s["truth"] + s["dare"]
    level = get_level(total)

    await update.message.reply_text(
        f"📊 Ігор: {s['games']}\n"
        f"🗣 Правда: {s['truth']}\n"
        f"😈 Дія: {s['dare']}\n"
        f"🏆 Рівень: {level}"
    )


# --- TOP ---
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if chat_id not in global_stats:
        await update.message.reply_text("Немає даних")
        return

    text = "🏆 Топ по іграм:\n"

    sorted_users = sorted(
        global_stats[chat_id].items(),
        key=lambda x: x[1]["games"],
        reverse=True
    )

    for i, (uid, data) in enumerate(sorted_users[:5]):
        user = await context.bot.get_chat_member(update.effective_chat.id, int(uid))
        text += f"{i+1}. {user.user.first_name} — {data['games']}\n"

    await update.message.reply_text(text)


# --- RUN ---
load_stats()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("top", top))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

print("БОТ ПРАЦЮЄ 🔥")

app.run_polling()
