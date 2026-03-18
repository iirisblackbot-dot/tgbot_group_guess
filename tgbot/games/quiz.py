import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

QUESTIONS = [
    {"q": "Какая планета самая большая в Солнечной системе?", "a": ["Юпитер", "Марс", "Земля", "Сатурн"], "correct": 0},
    {"q": "Кто написал 'Войну и мир'?", "a": ["Толстой", "Пушкин", "Достоевский", "Чехов"], "correct": 0},
    {"q": "Сколько материков на Земле?", "a": ["6", "5", "7", "4"], "correct": 0},
    {"q": "Какой химический элемент обозначается как Au?", "a": ["Золото", "Серебро", "Медь", "Железо"], "correct": 0},
    {"q": "В каком году человек впервые полетел в космос?", "a": ["1961", "1957", "1969", "1975"], "correct": 0},
    {"q": "Какая река самая длинная в мире?", "a": ["Амазонка", "Нил", "Янцзы", "Миссисипи"], "correct": 0},
    {"q": "Кто нарисовал 'Мона Лизу'?", "a": ["Да Винчи", "Пикассо", "Ван Гог", "Микеланджело"], "correct": 0},
    {"q": "Сколько секунд в одном часе?", "a": ["3600", "60", "360", "600"], "correct": 0},
    {"q": "Какая страна самая большая по площади?", "a": ["Россия", "Канада", "Китай", "США"], "correct": 0},
    {"q": "Какой океан самый глубокий?", "a": ["Тихий", "Атлантический", "Индийский", "Северный Ледовитый"], "correct": 0},
]

class Quiz:
    def __init__(self, sessions):
        self.sessions = sessions

    async def start(self, query, context, user_id):
        q_idx = random.randint(0, len(QUESTIONS) - 1)
        user_stats = self.sessions.get(user_id, {})
        user_stats.update({
            "game": "quiz",
            "q_idx": q_idx,
            "quiz_score": user_stats.get("quiz_score", 0)
        })
        self.sessions[user_id] = user_stats
        await self._show_question(query, q_idx, user_id)

    async def _show_question(self, query, q_idx, user_id):
        q_data = QUESTIONS[q_idx]
        text = f"🧠 *Викторина*\n\n{q_data['q']}"
        keyboard = [[InlineKeyboardButton(ans, callback_data=f"quiz_ans_{user_id}_{i}")] for i, ans in enumerate(q_data['a'])]
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle(self, query, context, data, user_id):
        parts = data.split("_")
        owner_id = int(parts[2])
        if user_id != owner_id:
            await query.answer("Это не твоя викторина! Начни свою в меню.", show_alert=True)
            return

        user_stats = self.sessions.get(user_id)
        if not user_stats or user_stats.get("game") != "quiz":
            return

        ans_idx = int(parts[3])
        q_idx = user_stats["q_idx"]
        q_data = QUESTIONS[q_idx]

        if ans_idx == q_data["correct"]:
            user_stats["quiz_score"] += 1
            res_text = "✅ *Правильно!* +1 балл."
        else:
            res_text = f"❌ *Неверно!* Правильный ответ: *{q_data['a'][q_data['correct']]}*."

        self.sessions[user_id] = user_stats
        text = (f"🧠 *Викторина*\n\n{res_text}\n📊 Твой счёт: {user_stats['quiz_score']}\n\nХочешь следующий вопрос?")
        keyboard = [[InlineKeyboardButton("➡️ Следующий вопрос", callback_data="game_quiz")],
                    [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
