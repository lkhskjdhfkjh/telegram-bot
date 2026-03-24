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
skip_used = 0

stats = {}
chat_stats = {}

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

    context.application.create_task(
        registration_timer(context, update.effective_chat.id, msg.message_id)
    )


# --- TIMER ---
async def registration_timer(context, chat_id, message_id):
    global registration_open, game_active

    for i in range(6):
        await asyncio.sleep(10)

    registration_open = False

    if len(players) < 2:
        await context.bot.send_message(chat_id, "❌ Мало гравців")
        return

    game_active = True

    if chat_id not in chat_stats:
        chat_stats[chat_id] = {"games": 0}
    chat_stats[chat_id]["games"] += 1

    for p in players:
        if p not in stats:
            stats[p] = {"games": 0}
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
        await update.message.reply_text(f"✅ {user.first_name} приєднався!")


# --- NEXT TURN ---
async def next_turn(context, chat_id):
    global current_player_index, waiting_end_turn, skip_used, turn_task

    if not game_active or not players:
        return

    if current_player_index >= len(players):
        current_player_index = 0

    user = await context.bot.get_chat(players[current_player_index])
    name = user.first_name
    player_id = user.id

    waiting_end_turn = False
    skip_used = 0

    keyboard = [["правда", "дія"], ["змінити (2)"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎯 {name}, твій хід!",
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
        "⏱ Час вийшов! Хід передано іншому"
    )

    await next_turn(context, chat_id)


# --- CHOICE ---
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player_index, waiting_end_turn, skip_used, turn_task

    if not update.message or not game_active:
        return

    user = update.message.from_user
    text = update.message.text.lower()

    if user.id != players[current_player_index]:
        return

    if not waiting_end_turn:

        if text == "змінити (2)":
            if skip_used >= 2:
                await update.message.reply_text("❌ Ліміт змін")
                return

            skip_used += 1
            await update.message.reply_text(f"🔄 Обери ще раз ({2 - skip_used})")
            return

        if text == "правда":
            await update.message.reply_text(random.choice(truths),
                                            reply_markup=ReplyKeyboardRemove())

        elif text == "дія":
            await update.message.reply_text(random.choice(dares),
                                            reply_markup=ReplyKeyboardRemove())

        else:
            return

        waiting_end_turn = True

        await update.message.reply_text(
            "✅ Натисни 'завершити хід'",
            reply_markup=ReplyKeyboardMarkup([["завершити хід"]], resize_keyboard=True)
        )

    elif text == "завершити хід":
        if turn_task:
            turn_task.cancel()

        current_player_index += 1
        waiting_end_turn = False

        await update.message.reply_text(
            "➡ Хід передано",
            reply_markup=ReplyKeyboardRemove()
        )

        await next_turn(context, update.effective_chat.id)


# --- TOP CHAT ---
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🏆 Топ цього чату:\n\n"

    sorted_users = sorted(stats.items(), key=lambda x: x[1]["games"], reverse=True)

    for i, (uid, s) in enumerate(sorted_users[:10], 1):
        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = "Гравець"

        text += f"{i}. {name} — {s['games']}\n"

    await update.message.reply_text(text)


# --- TOP ALL ---
async def topall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌍 Топ гравців:\n\n"

    sorted_users = sorted(stats.items(), key=lambda x: x[1]["games"], reverse=True)

    for i, (uid, s) in enumerate(sorted_users[:10], 1):
        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = "Гравець"

        text += f"{i}. {name} — {s['games']}\n"

    text += "\n🏆 Топ чатів:\n\n"

    sorted_chats = sorted(chat_stats.items(), key=lambda x: x[1]["games"], reverse=True)

    for i, (cid, s) in enumerate(sorted_chats[:10], 1):
        text += f"{i}. Чат {cid} — {s['games']}\n"

    await update.message.reply_text(text)


# --- HELP ---
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>Truth or Dare Bot</b>\n\n"

        "🎮 <b>Опис:</b>\n"
        "Бот для гри «Правда або Дія» у чаті.\n"
        "Гравці по черзі обирають дію.\n\n"

        "⚙️ <b>Команди:</b>\n"
        "/startgame — почати гру\n"
        "/join — приєднатись\n"
        "/leave — вийти\n"
        "/top — топ чату\n"
        "/topall — глобальний топ\n"
        "/help — допомога\n\n"

        "🎯 <b>Механіки:</b>\n"
        "• До 5 гравців\n"
        "• 60 сек реєстрація\n"
        "• 2 безкоштовних зміни\n"
        "• 3 хв на хід\n\n"

        "👑 Власник: (твій юз)\n"
        "📢 ТГК: (твій канал)\n\n"

        "💬 Ідеї/баги — пиши власнику"
    )

    await update.message.reply_text(text, parse_mode="HTML")


# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("topall", topall))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

app.run_polling()
