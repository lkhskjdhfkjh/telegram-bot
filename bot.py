from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import asyncio
import json
import os

TOKEN = "8527771101:AAFr_5QJhwhJsJgbwoVUjzxaveyIizFnkVc"

# --- ГРА ---
players = []
game_active = False
registration_open = False
current_player_index = 0
waiting_end_turn = False
turn_task = None

# --- МЕХАНІКИ ---
skip_used = 0
last_task = None

# --- СТАТИСТИКА ---
stats = {}
chat_stats = {}

# --- ФАЙЛ ЗБЕРЕЖЕННЯ ---
DATA_FILE = "data.json"


# --- ЗАВАНТАЖЕННЯ ---
def load_data():
    global stats, chat_stats

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            stats = data.get("stats", {})
            chat_stats = data.get("chat_stats", {})


# --- ЗБЕРЕЖЕННЯ ---
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "stats": stats,
            "chat_stats": chat_stats
        }, f)


# --- ПРАВДА / ДІЯ ---
truths = [
    "Який твій найбільший страх?",
    "Кого ти любиш найбільше (окрім родичів)?",
    "Який твій найбільший секрет?",
    "На що готовий заради коханої людини?",
    "Чи уникав ти колись зустрічі з кимось?",
    "Яка в тебе є дивна звичка?",
    "Кого ти б поцілував в цьому чаті, якби прийшлося обирати?",
    "Яку брехню ти казав що всі повірили?",
    "Що ти приховуєш від батьків?",
    "Про що ти шкодуєш найбільше?",
    "Що ти колись побачив, що тобі запам'яталось на все життя?",
    "Що про тебе думають інші, але це не правда?",
    "Якби тобі треба було себе чесно описати - що б ти сказав?",
    "Яку правду про себе тобі важко визнати?",
    "Коли ти востаннє плакав і чому?",
    "Що в собі ти не любиш?",
    "Який в тебе талант?",
    "Що (кого) боїшся втратити найбільше?",
    "Що останнє ти гуглив?",
    "Яка твоя улюблена гра?",
    "Який твій улюблений колір?",
    "Хто тобі здається найсимпатичнішим в чаті?",
    "Що б ти зробив, якби міг стати невидимкою на день?",
    "Коли ти востаннє брехав і чому?",
    "Що б ти в собі змінив, якби міг?",
    "Що тебе найбільше бісить в людях?",
    "Яка в тебе була найбільша сварка?",
    "Кому ти довіряєш найбільше?",
    "Якого питання ти боїшся найбільше?",
    "Якби можна було помінятися тілами на день, з ким би ти помінявся?"
]

dares = [
    "Зміни нік на 10 хвилин",
    "Зміни аватарку на 10 хвилин",
    "Скинь 13 фото з галереї",
    "Заспівай якусь пісню в голосове повідомлення",
    "Напиши четвертому по списку в чатах 'Я тебе люблю'",
    "Напиши перше що прийде в голову",
    "Пиши повідомлення тільки за допомогою емодзі 5 хвилин",
    "Пиши повідомлення тільки англійськими буквами 5 хвилин",
    "Покажи свою історію пошуку",
    "Скинь скрін останніх 3 чатів",
    "Відправ 13 фото з галереї",
    "Напиши комплімент людині, яку оберуть інші",
    "Дай іншим обрати слово, а ти повинен пояснити його за допомогою прикметників",
    "Запиши відео-рекламу будь-якого предмета (10 секунд)",
    "Нехай інші оберуть 10 емодзі, а ти повинен придумати історію з ними",
    "Коментуй наступні 15 повідомлень в чаті як журналіст",
    "Запиши голосове повідомлення, де ти смієшся як кінь без причини (20 сек)",
    "Напиши другу в особисті 'Дякую за все' і почекай реакції",
    "Відповідай на питання питаннями 5 хвилин",
    "Опиши себе словами на кожну букву імені",
    "Нехай інші придумають тобі роль і ти кажи від обличчя ролі 10 хвилин",
    "Три наступні хвилини пиши слова без букви А",
    "Опиши себе трьома словами",
    "Напиши комусь 'В нас проблеми' і чекай реакцію",
    "Напиши комусь 'Я все знаю' і чекай реакцію"
]

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active, registration_open, current_player_index

    if registration_open or game_active:
        await update.message.reply_text("❌ Гра вже йде або реєстрація відкрита")
        return

    # 🔐 перевірка прав
    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)

    if not bot_member.can_pin_messages:
        await update.message.reply_text("❌ Дай боту права на закріплення повідомлень")
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

    await context.bot.pin_chat_message(update.effective_chat.id, msg.message_id)

    context.application.create_task(
        registration_timer(context, update.effective_chat.id, msg.message_id)
    )
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

    # 📊 статистика
    chat_stats[str(chat_id)] = chat_stats.get(str(chat_id), {"games": 0})
    chat_stats[str(chat_id)]["games"] += 1

    for p in players:
        stats[str(p)] = stats.get(str(p), {"games": 0})
        stats[str(p)]["games"] += 1

    save_data()

    await context.bot.send_message(chat_id, "🎮 Гра почалась!")

    await next_turn(context, chat_id)
    async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not registration_open:
        return

    if len(players) >= 5:
        await update.message.reply_text("❌ Максимум 5 гравців")
        return

    user = update.message.from_user

    if user.id not in players:
        players.append(user.id)
        await update.message.reply_text(f"✅ {user.first_name} приєднався!")
        async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    user = update.message.from_user

    if user.id not in players:
        return

    players.remove(user.id)

    await update.message.reply_text(
        f"❌ {user.first_name} вийшов\n👥 Гравців: {len(players)}"
    )

    # ❗ якщо гра вже йде і мало гравців
    if game_active and len(players) < 2:
        game_active = False
        await update.message.reply_text("⛔ Гру зупинено (мало гравців)")

# --- CHOICE (FINAL NORMAL BUTTONS LIKE PHOTO 2) ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn, turn_task

    if not update.message or not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    # --- вибір правда/дія ---
    if not waiting_end_turn:

        # ❗ прибираємо кнопки одразу
        await update.message.reply_text(
            "🎲 Обробка...",
            reply_markup=ReplyKeyboardRemove()
        )

        if text == "правда":
            msg = random.choice(truths)
        elif text == "дія":
            msg = random.choice(dares)
        else:
            return

        # надсилаємо завдання БЕЗ кнопок
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📌 Завдання:\n{msg}"
        )

        # тепер тільки кнопка завершення (як окрема клавіатура внизу)
        keyboard = [["✅ завершити хід"]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )

        waiting_end_turn = True

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="👇 Натисни щоб передати хід",
            reply_markup=reply_markup
        )

    # --- завершення ---
    elif waiting_end_turn and "завершити" in text:

        if turn_task:
            turn_task.cancel()

        current_player_index += 1
        waiting_end_turn = False

        # ❗ повністю прибираємо клавіатуру
        await update.message.reply_text(
            "➡ Хід передано",
            reply_markup=ReplyKeyboardRemove()
        )

        await next_turn(context, update.effective_chat.id)
        # --- STATS (особиста статистика) ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    games = user_stats.get(user.id, {}).get("games", 0)
    truths_count = user_stats.get(user.id, {}).get("truths", 0)
    dares_count = user_stats.get(user.id, {}).get("dares", 0)

    await update.message.reply_text(
        f"📊 Статистика {user.first_name}:\n\n"
        f"🎮 Ігор: {games}\n"
        f"❓ Правда: {truths_count}\n"
        f"🔥 Дія: {dares_count}"
    )


# --- TOP CHAT ---
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_stats:
        await update.message.reply_text("❌ Немає даних")
        return

    sorted_users = sorted(user_stats.items(), key=lambda x: x[1].get("games", 0), reverse=True)

    text = "🏆 Топ гравців чату:\n\n"

    for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name
        except:
            name = "Unknown"

        text += f"{i}. {name} — {data.get('games',0)} ігор\n"

    await update.message.reply_text(text)


# --- GLOBAL TOP ---
async def topall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not global_stats:
        await update.message.reply_text("❌ Немає глобальних даних")
        return

    sorted_users = sorted(global_stats.items(), key=lambda x: x[1], reverse=True)

    text = "🌍 Глобальний топ гравців:\n\n"

    for i, (user_id, games) in enumerate(sorted_users[:10], start=1):
        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name
        except:
            name = "Unknown"

        text += f"{i}. {name} — {games} ігор\n"

    await update.message.reply_text(text)


# --- HELP ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Truth or Dare Bot\n\n"
        "🎮 Команди:\n"
        "/startgame — почати гру\n"
        "/join — приєднатись\n"
        "/leave — вийти\n"
        "/stats — твоя статистика\n"
        "/top — топ чату\n"
        "/topall — глобальний топ\n"
        "/help — допомога\n\n"
        "⚙️ Механіка:\n"
        "• До 5 гравців\n"
        "• 60 сек реєстрація\n"
        "• 3 хв на хід\n"
        "• 2 безкоштовні зміни завдання\n\n"
        "👑 Власник: (твій юз)\n"
        "📢 ТГК: (твій канал)\n\n"
        "💬 Ідеї / баги — пиши власнику"
    )


# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("topall", topall))
app.add_handler(CommandHandler("help", help_command))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

print("Бот запущений 🚀")
app.run_polling()
