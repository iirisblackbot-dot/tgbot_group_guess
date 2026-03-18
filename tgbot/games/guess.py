import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class GuessNumber:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_session_id(self, query):
        if query.inline_message_id:
            return query.inline_message_id
        return f"{query.from_user.id}"

    async def start(self, query, context, user_id):
        number = random.randint(1, 100)
        self.sessions[user_id] = {
            "game": "guess",
            "number": number,
            "attempts": 0,
            "waiting_for_guess": True
        }
        text = "🔢 *Угадай число*\n\nЯ загадал число от 1 до 100. Попробуй угадать его, написав число в чат!"
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    async def start_group(self, update, context):
        chat_id = update.effective_chat.id
        number = random.randint(1, 100)
        self.sessions[chat_id] = {
            "game": "guess_group",
            "number": number,
            "attempts": 0,
            "active": True
        }
        text = "🔢 *Угадай число (Групповая игра)*\n\nЯ загадал число от 1 до 100. Кто первым угадает? Пишите числа прямо в чат!"
        await update.message.reply_text(text, parse_mode="Markdown")

    async def handle_input(self, update, context, text, session_id):
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            guess = int(text)
        except ValueError:
            # В группах не отвечаем на не-числа, чтобы не спамить
            if session.get("game") == "guess":
                await update.message.reply_text("Пожалуйста, введи целое число!")
            return

        session["attempts"] += 1
        number = session["number"]
        user_name = update.effective_user.first_name

        if guess < number:
            await update.message.reply_text(f"📉 {user_name}: {guess} — Больше!")
        elif guess > number:
            await update.message.reply_text(f"📈 {user_name}: {guess} — Меньше!")
        else:
            await update.message.reply_text(
                f"🎉 *ПОБЕДА!*\n\n👤 {user_name} угадал число *{number}*!\nВсего попыток группы: {session['attempts']}",
                parse_mode="Markdown"
            )
            del self.sessions[session_id]

    # --- ИНЛАЙН РЕЖИМ (ДУЭЛЬ) ---

    async def start_multiplayer(self, query, context):
        session_id = query.inline_message_id
        user = query.from_user
        
        self.sessions[session_id] = {
            "game": "guess_duel",
            "creator_id": user.id,
            "creator_name": user.first_name,
            "target_id": None,
            "target_name": None,
            "number": None,
            "attempts": 0,
            "status": "waiting_number" # Ожидание загадывания числа
        }
        
        text = (f"🔢 *Угадай число (Дуэль)*\n\n"
                f"👤 {user.first_name} хочет сыграть!\n"
                f"Нажми кнопку ниже, чтобы загадать число (1-100).")
        
        keyboard = [[InlineKeyboardButton("🎲 Загадать число", callback_data="guess_set_num")]]
        await context.bot.edit_message_text(
            inline_message_id=session_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_callback(self, query, context, data, user_id):
        session_id = query.inline_message_id
        session = self.sessions.get(session_id)
        if not session:
            await query.answer("Сессия не найдена!", show_alert=True)
            return

        if data == "guess_set_num":
            if user_id != session["creator_id"]:
                await query.answer("Только создатель может загадать число!", show_alert=True)
                return
            
            # В инлайне мы не можем получить текстовый ввод напрямую, 
            # поэтому предложим выбрать диапазон или случайное для простоты, 
            # либо попросим написать боту в ЛС (но это сложно для инлайна).
            # Сделаем выбор из кнопок для загадывания (диапазоны).
            text = "🔢 Выбери число, которое хочешь загадать:"
            keyboard = []
            for i in range(0, 100, 20):
                row = [InlineKeyboardButton(str(j), callback_data=f"guess_val_{j}") for j in range(i+1, i+6)]
                keyboard.append(row)
            
            await context.bot.edit_message_text(
                inline_message_id=session_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data.startswith("guess_val_"):
            if user_id != session["creator_id"]:
                await query.answer("Не ты загадываешь!", show_alert=True)
                return
            
            val = int(data.split("_")[2])
            session["number"] = val
            session["status"] = "guessing"
            
            text = (f"🔢 *Угадай число (Дуэль)*\n\n"
                    f"👤 {session['creator_name']} загадал число!\n"
                    f"Кто первым угадает? Пишите числа ответом на это сообщение!")
            
            await context.bot.edit_message_text(
                inline_message_id=session_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
            )

    async def handle_multi_input(self, update, context, text, user_id, session_id):
        session = self.sessions.get(session_id)
        if not session or session.get("status") != "guessing":
            return

        if user_id == session["creator_id"]:
            # Создатель не может угадывать свое число
            return

        try:
            guess = int(text)
        except ValueError:
            return

        session["attempts"] += 1
        number = session["number"]
        user_name = update.effective_user.first_name

        if guess == number:
            res_text = (f"🎉 *ПОБЕДА!*\n\n"
                        f"👤 {user_name} угадал число *{number}*!\n"
                        f"Загадано было: {session['creator_name']}\n"
                        f"Всего попыток: {session['attempts']}")
            
            # Обновляем инлайн сообщение
            await context.bot.edit_message_text(
                inline_message_id=session_id,
                text=res_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
            )
            del self.sessions[session_id]
        else:
            # Можно отправлять подсказки в чат ответом
            hint = "Больше!" if guess < number else "Меньше!"
            await update.message.reply_text(f"🔢 {user_name}: {guess} — {hint}")
