import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

WORDS = ["ПРОГРАММИСТ", "ТЕЛЕГРАМ", "МАЙНКРАФТ", "КАЗИНО", "РИСОВАНИЕ", "МОРСКОЙ", "КРЕСТИКИ", "НОЛИКИ", "КАМЕНЬ", "НОЖНИЦЫ", "БУМАГА", "ЗМЕЙКА", "ВИКТОРИНА", "ГОРОДА", "ВИСЕЛИЦА"]

HANGMAN_STAGES = [
    "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n========="
]

class Hangman:
    def __init__(self, sessions):
        self.sessions = sessions

    async def start(self, query, context, user_id):
        word = random.choice(WORDS)
        self.sessions[user_id] = {
            "game": "hangman",
            "word": word,
            "guessed": [],
            "errors": 0,
            "waiting_for_letter": True,
            "chat_id": query.message.chat_id if query.message else None
        }
        await self._show_game(query, user_id)

    async def _show_game(self, query, user_id):
        session = self.sessions[user_id]
        display_word = "".join([c if c in session["guessed"] else "_" for c in session["word"]])
        text = (f"🧩 *Виселица*\n\n```\n{HANGMAN_STAGES[session['errors']]}\n```\n"
                f"Слово: `{display_word}`\nОшибки: {session['errors']}/6\n\nНапиши букву (на русском), чтобы угадать!")
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]))

    async def handle_input(self, update, context, text, user_id):
        session = self.sessions.get(user_id)
        if not session or session.get("game") != "hangman" or not session.get("waiting_for_letter"):
            return

        letter = text.upper().strip()
        if len(letter) != 1 or not letter.isalpha():
            return

        if letter in session["guessed"]:
            await update.message.reply_text("Ты уже называл эту букву!")
            return

        session["guessed"].append(letter)
        if letter not in session["word"]:
            session["errors"] += 1

        display_word = "".join([c if c in session["guessed"] else "_" for c in session["word"]])
        if "_" not in display_word:
            session["waiting_for_letter"] = False
            await update.message.reply_text(f"🎉 *Победа!* Ты угадал слово: *{session['word']}*!", parse_mode="Markdown", reply_markup=self._get_finish_keyboard())
            return
        
        if session["errors"] >= 6:
            session["waiting_for_letter"] = False
            await update.message.reply_text(f"💀 *Поражение!* Загаданное слово было: *{session['word']}*.\n```\n{HANGMAN_STAGES[6]}\n```", parse_mode="Markdown", reply_markup=self._get_finish_keyboard())
            return

        text = (f"🧩 *Виселица*\n\n```\n{HANGMAN_STAGES[session['errors']]}\n```\n"
                f"Слово: `{display_word}`\nОшибки: {session['errors']}/6\n\nБуква '{letter}' принята! Продолжай.")
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]))

    def _get_finish_keyboard(self):
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Играть снова", callback_data="game_hangman"),
                                      InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
