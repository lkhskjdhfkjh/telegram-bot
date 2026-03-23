from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random

TOKEN = "8699261089:AAHUKDhXNgUVkHNyOpkXHatlTRUZzM53n4U"

players = []
game_active = False
current_player_index = 0
player_stats = {}
waiting_end_turn = False

# 📊 глобальна статистика
global_stats = {}

truths = ["Твій страх?", "Кого любиш?", "Твій секрет?"]
dares = ["Зміни нік", "Напиши крінж", "Скинь селфі"]


def init_user(user_id):
    if user_id not in global_stats:
        global_stats[user_id] = {
            "games": 0,
            "truth": 0,
            "dare": 0
        }


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пиши /startgame 😈")


# --- START GAME ---
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, current_player_index, player_stats

    players = []
    player_stats = {}
    game_active = False
    current_player_index = 0

    await update.message.reply_text("🔥 /join\n/begin (макс 4)")


# --- JOIN ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if len(players) >= 4:
        await update.message.reply_text("❌ Макс 4")
        return

    if user.id not in players:
        players.append(user.id)
        player_stats[user.id] = {"truth": 0, "dare": 0}
        init_user(user.id)

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


# --- BEGIN ---
async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    if len(players) < 2:
        await update.message.reply_text("❌ Мінімум 2")
        return

    game_active = True

    # 📊 рахуємо гру
    for p in players:
        init_user(p)
        global_stats[p]["games"] += 1

    await update.message.reply_text("🎮 Старт!")

    await next_turn(update, context)


# --- NEXT TURN ---
async def next_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn

    if current_player_index >= len(players):
        current_player_index = 0

    player_id = players[current_player_index]
    user = await context.bot.get_chat_member(update.effective_chat.id, player_id)

    waiting_end_turn = False

    keyboard = [["правда", "дія"]]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎯 {user.user.first_name}, твій хід",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn

    if not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    if waiting_end_turn:
        if text == "завершити хід":
            current_player_index += 1
            await next_turn(update, context)
        return

    if text == "правда":
        global_stats[user.id]["truth"] += 1

        await update.message.reply_text(
            random.choice(truths),
            reply_markup=ReplyKeyboardMarkup([["завершити хід"]], resize_keyboard=True)
        )

        waiting_end_turn = True

    elif text == "дія":
        global_stats[user.id]["dare"] += 1

        await update.message.reply_text(
            random.choice(dares),
            reply_markup=ReplyKeyboardMarkup([["завершити хід"]], resize_keyboard=True)
        )

        waiting_end_turn = True


# --- STATS ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    init_user(user.id)

    s = global_stats[user.id]

    total = s["truth"] + s["dare"]

    await update.message.reply_text(
        f"📊 Твоя статистика:\n"
        f"🎮 Ігор: {s['games']}\n"
        f"🗣 Правда: {s['truth']}\n"
        f"😈 Дія: {s['dare']}\n"
        f"📊 Всього: {total}"
    )


# --- TOP ---
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not global_stats:
        await update.message.reply_text("Немає даних")
        return

    text = "🏆 Рейтинг:\n"

    sorted_users = sorted(global_stats.items(), key=lambda x: x[1]["truth"] + x[1]["dare"], reverse=True)

    for i, (uid, data) in enumerate(sorted_users[:5]):
        user = await context.bot.get_chat_member(update.effective_chat.id, uid)
        total = data["truth"] + data["dare"]

        text += f"{i+1}. {user.user.first_name} — {total}\n"

    await update.message.reply_text(text)


# --- APP ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(CommandHandler("begin", begin))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("top", top))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

app.run_polling()
