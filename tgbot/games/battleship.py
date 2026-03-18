import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

EMPTY = "🟦"
SHIP = "🟦"   # корабли скрыты
SHIP_VISIBLE = "🟩"  # для игрока
HIT = "💥"
MISS = "🌊"
SUNK = "🔥"

GRID_SIZE = 7
SHIPS = [3, 3, 2, 2, 1, 1, 1]
TOTAL_CELLS = sum(SHIPS)

class BattleshipGame:
    def __init__(self):
        self.player_grid = [[EMPTY]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.bot_grid = [[EMPTY]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.bot_ships = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.player_ships = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.bot_hits = 0
        self.player_hits = 0
        self.total_ship_cells = TOTAL_CELLS
        self.bot_memory = []
        self.place_ships(self.bot_ships)
        self.place_ships(self.player_ships)

    def place_ships(self, grid):
        for ship_len in SHIPS:
            placed = False
            attempts = 0
            while not placed and attempts < 1000:
                attempts += 1
                horiz = random.choice([True, False])
                if horiz:
                    r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - ship_len)
                    cells = [(r, c+i) for i in range(ship_len)]
                else:
                    r, c = random.randint(0, GRID_SIZE - ship_len), random.randint(0, GRID_SIZE - 1)
                    cells = [(r+i, c) for i in range(ship_len)]

                ok = True
                for (rr, cc) in cells:
                    for dr in [-1,0,1]:
                        for dc in [-1,0,1]:
                            nr, nc = rr+dr, cc+dc
                            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                                if grid[nr][nc]: ok = False
                if ok:
                    for (rr, cc) in cells: grid[rr][cc] = True
                    placed = True

    def bot_shoot(self):
        if self.bot_memory:
            r, c = self.bot_memory.pop(0)
        else:
            available = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.player_grid[r][c] == EMPTY]
            if not available: return None
            r, c = random.choice(available)

        if self.player_grid[r][c] in [HIT, MISS, SUNK]: return self.bot_shoot()

        if self.player_ships[r][c]:
            self.player_grid[r][c] = HIT
            self.bot_hits += 1
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                    if self.player_grid[nr][nc] == EMPTY: self.bot_memory.insert(0, (nr, nc))
            return (r, c, True)
        else:
            self.player_grid[r][c] = MISS
            return (r, c, False)

class Battleship:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_session_id(self, query):
        if query.inline_message_id: return query.inline_message_id
        return f"{query.message.chat_id}_{query.message.message_id}"

    def render_grid(self, grid, ships=None, hide_ships=True):
        rows = []
        for r in range(GRID_SIZE):
            cells = []
            for c in range(GRID_SIZE):
                cell = grid[r][c]
                if cell == EMPTY and not hide_ships and ships and ships[r][c]: cells.append(SHIP_VISIBLE)
                else: cells.append(cell)
            rows.append("".join(cells))
        return "\n".join(rows)

    def get_multi_keyboard(self, game_over=False):
        if game_over: return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
        keyboard = []
        for r in range(GRID_SIZE):
            row = [InlineKeyboardButton("·", callback_data=f"bs_m_sh_{r}_{c}") for c in range(GRID_SIZE)]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    async def start_multiplayer(self, query, context):
        user = query.from_user
        session_id = self.get_session_id(query)
        self.sessions[session_id] = {
            "game": "bs_multi",
            "p1_id": user.id,
            "p1_name": user.first_name,
            "p2_id": None,
            "p1_ships": [[False]*GRID_SIZE for _ in range(GRID_SIZE)],
            "p2_ships": [[False]*GRID_SIZE for _ in range(GRID_SIZE)],
            "p1_grid": [[EMPTY]*GRID_SIZE for _ in range(GRID_SIZE)],
            "p2_grid": [[EMPTY]*GRID_SIZE for _ in range(GRID_SIZE)],
            "p1_hits": 0,
            "p2_hits": 0,
            "turn": "p1",
            "phase": "joining"
        }
        await query.answer("Вызов принят!")
        text = (f"🚢 *Морской бой*\n\n"
                f"👤 {user.first_name} ждет противника...\n"
                f"Нажми кнопку ниже, чтобы вступить в бой!")
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚢 Вступить в бой", callback_data="bs_m_join")]])
        if query.inline_message_id:
            await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)

    async def handle(self, query, context, data, user_id):
        session_id = self.get_session_id(query)
        
        if data == "game_battleship":
            game = BattleshipGame()
            user_stats = self.sessions.get(user_id, {})
            self.sessions[session_id] = {"game": "battleship", "bs_game": game, "user_id": user_id}
            text = self._build_single_text(game, user_stats.get("bs_wins", 0), user_stats.get("bs_losses", 0), "🎯 Стреляй!")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self._get_single_keyboard(game))
            return

        if data.startswith("bs_shoot_"):
            parts = data.split("_")
            r, c = int(parts[2]), int(parts[3])
            session = self.sessions.get(session_id)
            if not session or "bs_game" not in session: return
            game = session["bs_game"]
            u_id = session["user_id"]
            user_stats = self.sessions.get(u_id, {})

            if game.bot_ships[r][c]:
                game.bot_grid[r][c] = HIT
                game.player_hits += 1
                res = "💥 Попал!"
            else:
                game.bot_grid[r][c] = MISS
                res = "🌊 Мимо!"
                game.bot_shoot()

            if game.player_hits >= TOTAL_CELLS:
                user_stats["bs_wins"] = user_stats.get("bs_wins", 0) + 1
                self.sessions[u_id] = user_stats
                await query.edit_message_text(f"🏆 *Ты победил!*\n\n📊 Счёт: 🏆{user_stats['bs_wins']} / 💀{user_stats.get('bs_losses', 0)}", parse_mode="Markdown", reply_markup=self.get_multi_keyboard(game_over=True))
                if session_id in self.sessions: del self.sessions[session_id]
                return
            if game.bot_hits >= TOTAL_CELLS:
                user_stats["bs_losses"] = user_stats.get("bs_losses", 0) + 1
                self.sessions[u_id] = user_stats
                await query.edit_message_text(f"💀 *Бот победил!*\n\n📊 Счёт: 🏆{user_stats.get('bs_wins', 0)} / 💀{user_stats['bs_losses']}", parse_mode="Markdown", reply_markup=self.get_multi_keyboard(game_over=True))
                if session_id in self.sessions: del self.sessions[session_id]
                return

            await query.edit_message_text(self._build_single_text(game, user_stats.get("bs_wins", 0), user_stats.get("bs_losses", 0), res), parse_mode="Markdown", reply_markup=self._get_single_keyboard(game))
            return

        if data.startswith("bs_m_"):
            session = self.sessions.get(session_id)
            if not session:
                await query.answer("Сессия игры не найдена.", show_alert=True)
                return

            if data == "bs_m_join":
                if user_id == session["p1_id"]:
                    await query.answer("Ты уже в игре!", show_alert=True)
                    return
                session["p2_id"] = user_id
                session["p2_name"] = query.from_user.first_name
                session["phase"] = "playing"
                self._auto_place(session["p1_ships"])
                self._auto_place(session["p2_ships"])
                await self._update_multi_msg(query, session, context)
                return

            if data.startswith("bs_m_sh_"):
                parts = data.split("_")
                r, c = int(parts[3]), int(parts[4])
                current_p = "p1" if session["turn"] == "p1" else "p2"
                current_id = session["p1_id"] if session["turn"] == "p1" else session["p2_id"]
                
                if user_id != current_id:
                    await query.answer("Сейчас не твой ход!", show_alert=True)
                    return
                
                target_grid = session["p2_grid"] if session["turn"] == "p1" else session["p1_grid"]
                target_ships = session["p2_ships"] if session["turn"] == "p1" else session["p1_ships"]
                
                if target_grid[r][c] != EMPTY:
                    await query.answer("Сюда уже стреляли!", show_alert=True)
                    return
                
                if target_ships[r][c]:
                    target_grid[r][c] = HIT
                    session[f"{session['turn']}_hits"] += 1
                    hit_msg = "💥 Попал!"
                else:
                    target_grid[r][c] = MISS
                    session["turn"] = "p2" if session["turn"] == "p1" else "p1"
                    hit_msg = "🌊 Мимо!"

                if session[f"{current_p}_hits"] >= TOTAL_CELLS:
                    winner_name = session[f"{current_p}_name"] if current_p == "p2" else session["p1_name"]
                    text = (f"🚢 *Морской бой*\n\n🏆 *{winner_name} победил!* Все корабли потоплены!\n\n"
                            f"👤 {session['p1_name']} VS {session.get('p2_name', '???')}")
                    if query.inline_message_id:
                        await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=self.get_multi_keyboard(game_over=True))
                    else:
                        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=self.get_multi_keyboard(game_over=True))
                    if session_id in self.sessions: del self.sessions[session_id]
                    return

                await query.answer(hit_msg)
                await self._update_multi_msg(query, session, context)

    def _auto_place(self, ships_grid):
        for ship_len in SHIPS:
            placed = False
            while not placed:
                horiz = random.choice([True, False])
                if horiz:
                    r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-ship_len)
                    cells = [(r, c+i) for i in range(ship_len)]
                else:
                    r, c = random.randint(0, GRID_SIZE-ship_len), random.randint(0, GRID_SIZE-1)
                    cells = [(r+i, c) for i in range(ship_len)]
                if all(not ships_grid[rr][cc] for rr, cc in cells):
                    for rr, cc in cells: ships_grid[rr][cc] = True
                    placed = True

    async def _update_multi_msg(self, query, session, context):
        turn_name = session["p1_name"] if session["turn"] == "p1" else session["p2_name"]
        turn_emoji = "🔴" if session["turn"] == "p1" else "🔵"
        session_id = self.get_session_id(query)
        text = (f"🚢 *Морской бой*\n\n"
                f"Ход: {turn_emoji} *{turn_name}*\n\n"
                f"🔴 {session['p1_name']}: {session['p1_hits']}/{TOTAL_CELLS} 💥\n"
                f"🔵 {session['p2_name']}: {session['p2_hits']}/{TOTAL_CELLS} 💥\n\n"
                f"🎯 Нажимай на кнопки ниже, чтобы стрелять по полю противника!")
        if query.inline_message_id:
            await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=self.get_multi_keyboard())
        else:
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=self.get_multi_keyboard())

    def _get_single_keyboard(self, game):
        keyboard = []
        for r in range(GRID_SIZE):
            row = []
            for c in range(GRID_SIZE):
                cell = game.bot_grid[r][c]
                cb = "bs_noop" if cell in [HIT, MISS, SUNK] else f"bs_shoot_{r}_{c}"
                row.append(InlineKeyboardButton(cell if cell in [HIT, MISS, SUNK] else "·", callback_data=cb))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    def _build_single_text(self, game, wins, losses, status):
        player_grid_str = self.render_grid(game.player_grid, game.player_ships, hide_ships=False)
        return (f"🚢 *Морской бой*\n"
                f"📊 Счёт: 🏆{wins} / 💀{losses}\n\n"
                f"*Твоё поле:*\n`{player_grid_str}`\n\n"
                f"{status}")
