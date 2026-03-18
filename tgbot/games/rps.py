import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CHOICES = {
    "rock": "🪨 Камень",
    "scissors": "✂️ Ножницы",
    "paper": "📄 Бумага",
}

BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}

class RPS:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_session_id(self, query):
        if query.inline_message_id:
            return query.inline_message_id
        return f"{query.message.chat_id}_{query.message.message_id}"

    def get_choice_keyboard(self):
        keyboard = [
            [
                InlineKeyboardButton("🪨 Камень", callback_data="rps_rock"),
                InlineKeyboardButton("✂️ Ножницы", callback_data="rps_scissors"),
                InlineKeyboardButton("📄 Бумага", callback_data="rps_paper"),
            ],
            [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_result_keyboard(self):
        keyboard = [[
            InlineKeyboardButton("🔄 Играть снова", callback_data="game_rps"),
            InlineKeyboardButton("🏠 Меню", callback_data="main_menu"),
        ]]
        return InlineKeyboardMarkup(keyboard)

    async def start_multiplayer(self, query, context):
        user = query.from_user
        session_id = self.get_session_id(query)
        self.sessions[session_id] = {
            "game": "rps_multi",
            "p1_id": user.id,
            "p1_name": user.first_name,
            "p2_id": None,
            "p1_choice": None,
            "p2_choice": None,
        }
        await query.answer("Вызов принят!")
        text = (f"✂️ *Камень-Ножницы-Бумага*\n\n"
                f"👤 {user.first_name} ждет противника...\n"
                f"Нажми кнопку ниже, чтобы вступить в игру!")
        
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("👊 Вступить в игру", callback_data="rps_m_join")]])
        
        if query.inline_message_id:
            await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

    async def handle(self, query, context, data, user_id):
        session_id = self.get_session_id(query)
        
        if data.startswith("rps_m_"):
            session = self.sessions.get(session_id)
            if not session:
                await query.answer("Сессия игры не найдена.", show_alert=True)
                return
            
            if data == "rps_m_join":
                if user_id == session["p1_id"]:
                    await query.answer("Ты уже в игре!", show_alert=True)
                    return
                session["p2_id"] = user_id
                session["p2_name"] = query.from_user.first_name
                text = (f"✂️ *Камень-Ножницы-Бумага*\n\n"
                        f"👤 {session['p1_name']} VS {session['p2_name']}\n\n"
                        f"Делайте ваши ходы!")
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🪨", callback_data="rps_m_move_rock"),
                    InlineKeyboardButton("✂️", callback_data="rps_m_move_scissors"),
                    InlineKeyboardButton("📄", callback_data="rps_m_move_paper"),
                ]])
                if query.inline_message_id:
                    await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
                else:
                    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)
                return

            if data.startswith("rps_m_move_"):
                choice = data.split("_")[3]
                if user_id == session["p1_id"]:
                    if session["p1_choice"]:
                        await query.answer("Ты уже сделал ход!", show_alert=True)
                        return
                    session["p1_choice"] = choice
                elif user_id == session["p2_id"]:
                    if session["p2_choice"]:
                        await query.answer("Ты уже сделал ход!", show_alert=True)
                        return
                    session["p2_choice"] = choice
                else:
                    await query.answer("Ты не участвуешь в этой игре!", show_alert=True)
                    return

                if session["p1_choice"] and session["p2_choice"]:
                    p1_c, p2_c = session["p1_choice"], session["p2_choice"]
                    if p1_c == p2_c: res = "🤝 Ничья!"
                    elif BEATS[p1_c] == p2_c: res = f"🏆 {session['p1_name']} победил!"
                    else: res = f"🏆 {session['p2_name']} победил!"
                    
                    text = (f"✂️ *Камень-Ножницы-Бумага*\n\n"
                            f"{session['p1_name']}: {CHOICES[p1_c]}\n"
                            f"{session['p2_name']}: {CHOICES[p2_c]}\n\n"
                            f"✨ {res}")
                    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
                    
                    if query.inline_message_id:
                        await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
                    else:
                        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)
                    if session_id in self.sessions: del self.sessions[session_id]
                else:
                    await query.answer("Ход принят! Ждем второго игрока.")
                return

        if data == "game_rps":
            if user_id not in self.sessions:
                self.sessions[user_id] = {"rps_wins": 0, "rps_losses": 0, "rps_draws": 0}
            user_stats = self.sessions[user_id]
            text = (f"✂️ *Камень-Ножницы-Бумага*\n\n"
                    f"📊 Счёт: 🏆{user_stats["rps_wins"]} / 💀{user_stats["rps_losses"]} / 🤝{user_stats["rps_draws"]}\n\n"
                    f"Выбери свой ход:")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_choice_keyboard())
            return

        choice_map = {"rps_rock": "rock", "rps_scissors": "scissors", "rps_paper": "paper"}
        if data in choice_map:
            player_choice = choice_map[data]
            bot_choice = random.choice(list(CHOICES.keys()))
            if user_id not in self.sessions:
                self.sessions[user_id] = {"rps_wins": 0, "rps_losses": 0, "rps_draws": 0}
            user_stats = self.sessions[user_id]
            
            if player_choice == bot_choice:
                user_stats["rps_draws"] += 1
                result = "🤝 *Ничья!*"
            elif BEATS[player_choice] == bot_choice:
                user_stats["rps_wins"] += 1
                result = "🏆 *Ты победил!*"
            else:
                user_stats["rps_losses"] += 1
                result = "💀 *Бот победил!*"

            self.sessions[user_id] = user_stats
            text = (f"✂️ *Камень-Ножницы-Бумага*\n\n"
                    f"Ты выбрал: {CHOICES[player_choice]}\n"
                    f"Бот выбрал: {CHOICES[bot_choice]}\n\n"
                    f"{result}\n\n"
                    f"📊 Счёт: 🏆{user_stats["rps_wins"]} / 💀{user_stats["rps_losses"]} / 🤝{user_stats["rps_draws"]}")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_result_keyboard())
