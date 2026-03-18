import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

WIDTH, HEIGHT = 10, 10
EMPTY, SNAKE, FOOD, HEAD = "⬜", "🟩", "🍎", "🐲"

class Snake:
    def __init__(self, sessions):
        self.sessions = sessions

    async def start(self, query, context, user_id):
        snake = [(5, 5), (5, 4), (5, 3)]
        self.sessions[user_id] = {
            "game": "snake",
            "snake": snake,
            "food": self._spawn_food(snake),
            "direction": "RIGHT",
            "score": 0,
            "game_over": False
        }
        await self._show_game(query, user_id)

    def _spawn_food(self, snake):
        while True:
            food = (random.randint(0, HEIGHT-1), random.randint(0, WIDTH-1))
            if food not in snake: return food

    async def _show_game(self, query, user_id):
        session = self.sessions[user_id]
        grid = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
        fr, fc = session["food"]
        grid[fr][fc] = FOOD
        for i, (r, c) in enumerate(session["snake"]):
            if 0 <= r < HEIGHT and 0 <= c < WIDTH:
                grid[r][c] = HEAD if i == 0 else SNAKE
        board_str = "\n".join(["".join(row) for row in grid])
        text = f"🐍 *Змейка*\n\n{board_str}\n\nСчёт: {session['score']}"
        if session["game_over"]:
            text += "\n\n💀 *ИГРА ОКОНЧЕНА!*"
            keyboard = [[InlineKeyboardButton("🔄 Играть снова", callback_data="game_snake")],
                        [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]
        else:
            keyboard = [[InlineKeyboardButton("🔼", callback_data=f"snake_up_{user_id}")],
                        [InlineKeyboardButton("◀️", callback_data=f"snake_left_{user_id}"), 
                         InlineKeyboardButton("▶️", callback_data=f"snake_right_{user_id}")],
                        [InlineKeyboardButton("🔽", callback_data=f"snake_down_{user_id}")],
                        [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle(self, query, context, data, user_id):
        parts = data.split("_")
        owner_id = int(parts[2])
        if user_id != owner_id:
            await query.answer("Это не твоя змейка! Начни свою в меню.", show_alert=True)
            return
        session = self.sessions.get(user_id)
        if not session or session.get("game") != "snake" or session["game_over"]: return
        direction = parts[1].upper()
        opp = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if direction != opp.get(session["direction"]): session["direction"] = direction
        head_r, head_c = session["snake"][0]
        if session["direction"] == "UP": head_r -= 1
        elif session["direction"] == "DOWN": head_r += 1
        elif session["direction"] == "LEFT": head_c -= 1
        elif session["direction"] == "RIGHT": head_c += 1
        if head_r < 0 or head_r >= HEIGHT or head_c < 0 or head_c >= WIDTH or (head_r, head_c) in session["snake"]:
            session["game_over"] = True
        else:
            new_head = (head_r, head_c)
            session["snake"].insert(0, new_head)
            if new_head == session["food"]:
                session["score"] += 1
                session["food"] = self._spawn_food(session["snake"])
            else: session["snake"].pop()
        await self._show_game(query, user_id)
