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
    "Що(кого) боїшся втратити найбільше?",
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
    "Якого питання ти боїшся найбільше?"
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
    "Дай іншим обрати слово а ти повинен пояснити його за допомогою прикметників",
    "Запиши відео-рекламу будь якого предмета (10 секунд)",
    "Нехай інші оберуть 10 емодзі а ти повинен придумати історію з ними",
    "Коментуй наступні 15 повідомлень в чату як журналіст",
    "Запиши голосове повідомлення де ти смієшся як кінь без причини (20 сек)",
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


# --- LEAVE (FIXED) ---
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active

    user = update.message.from_user

    if user.id not in players:
        return

    players.remove(user.id)

    await update.message.reply_text(
        f"❌ {user.first_name} вийшов\n👥 Гравців: {len(players)}"
    )

    # ❗ якщо гра ще не почалась — нічого не робимо
    if not game_active:
        return

    # якщо під час гри стало мало гравців
    if len(players) < 2:
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
            coins[user.id] += 5
            await update.message.reply_text(
                random.choice(truths),
                reply_markup=ReplyKeyboardRemove()
            )

        elif text == "дія":
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice))

app.run_polling()
