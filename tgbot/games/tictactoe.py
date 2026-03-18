import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

EMPTY = "⬜"
X = "❌"
O = "⭕"

class TicTacToe:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_session_id(self, query):
        if query.inline_message_id:
            return query.inline_message_id
        return f"{query.message.chat_id}_{query.message.message_id}"

    def new_game(self, session_id, user_id):
        # Сохраняем статистику пользователя, если она есть
        user_stats = self.sessions.get(user_id, {})
        self.sessions[session_id] = {
            "game": "ttt",
            "board": [EMPTY] * 9,
            "player": X,
            "user_id": user_id,
            "ttt_wins": user_stats.get("ttt_wins", 0),
            "ttt_losses": user_stats.get("ttt_losses", 0),
            "ttt_draws": user_stats.get("ttt_draws", 0),
        }
        return self.sessions[session_id]

    def get_board_keyboard(self, board, game_over=False, multi=False):
        keyboard = []
        for row in range(3):
            kb_row = []
            for col in range(3):
                idx = row * 3 + col
                cell = board[idx]
                if game_over or cell != EMPTY:
                    cb = f"ttt_noop_{idx}"
                else:
                    if multi:
                        cb = f"ttt_m_{idx}"
                    else:
                        cb = f"ttt_move_{idx}"
                kb_row.append(InlineKeyboardButton(cell, callback_data=cb))
            keyboard.append(kb_row)
        
        if game_over:
            if multi:
                keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
            else:
                keyboard.append([
                    InlineKeyboardButton("🔄 Играть снова", callback_data="game_ttt"),
                    InlineKeyboardButton("🏠 Меню", callback_data="main_menu"),
                ])
        return InlineKeyboardMarkup(keyboard)

    def check_winner(self, board):
        wins = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a,b,c in wins:
            if board[a] == board[b] == board[c] and board[a] != EMPTY:
                return board[a]
        if EMPTY not in board:
            return "draw"
        return None

    def bot_move(self, board):
        def minimax(b, is_max):
            w = self.check_winner(b)
            if w == O: return 10
            if w == X: return -10
            if w == "draw": return 0
            if is_max:
                best = -100
                for i in range(9):
                    if b[i] == EMPTY:
                        b[i] = O
                        best = max(best, minimax(b, False))
                        b[i] = EMPTY
                return best
            else:
                best = 100
                for i in range(9):
                    if b[i] == EMPTY:
                        b[i] = X
                        best = min(best, minimax(b, True))
                        b[i] = EMPTY
                return best

        best_val = -100
        best_move = -1
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = O
                val = minimax(board, False)
                board[i] = EMPTY
                if val > best_val:
                    best_val = val
                    best_move = i
        return best_move

    async def start_multiplayer(self, query, context):
        user = query.from_user
        session_id = self.get_session_id(query)
        self.sessions[session_id] = {
            "game": "ttt_multi",
            "board": [EMPTY] * 9,
            "player_x": None,
            "player_o": user.id,
            "player_o_name": user.first_name,
            "turn": X,
        }
        await query.answer("Вызов принят!")
        
        text = (f"⚔️ *Крестики-нолики*\n\n"
                f"⭕ {user.first_name} ждет противника...\n"
                f"Нажми на любую клетку, чтобы стать ❌ и сделать ход!")
        
        if query.inline_message_id:
            await context.bot.edit_message_text(
                inline_message_id=session_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=self.get_board_keyboard(self.sessions[session_id]["board"], multi=True)
            )
        else:
            await query.edit_message_text(
                text=text,
                parse_mode="Markdown",
                reply_markup=self.get_board_keyboard(self.sessions[session_id]["board"], multi=True)
            )

    async def handle(self, query, context, data, user_id):
        session_id = self.get_session_id(query)
        
        if data == "game_ttt":
            session = self.new_game(session_id, user_id)
            text = (f"⚔️ *Крестики-нолики*\n\n"
                    f"Ты играешь за ❌, бот за ⭕\n"
                    f"📊 Счёт: 🏆{session['ttt_wins']} / 💀{session['ttt_losses']} / 🤝{session['ttt_draws']}\n\n"
                    f"Твой ход!")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(session["board"]))
            return

        if data.startswith("ttt_m_"):
            idx = int(data.split("_")[3])
            session = self.sessions.get(session_id)
            if not session:
                await query.answer("Сессия игры не найдена. Начните новую игру.", show_alert=True)
                return

            board = session["board"]
            if session["player_x"] is None:
                if user_id == session["player_o"]:
                    await query.answer("Жди противника!", show_alert=True)
                    return
                session["player_x"] = user_id
                session["player_x_name"] = query.from_user.first_name

            current_player = session["player_x"] if session["turn"] == X else session["player_o"]
            if user_id != current_player:
                await query.answer("Сейчас не твой ход!", show_alert=True)
                return

            board[idx] = session["turn"]
            winner = self.check_winner(board)
            
            if winner:
                if winner == "draw": res = "🤝 Ничья!"
                else:
                    name = session["player_x_name"] if winner == X else session["player_o_name"]
                    res = f"🏆 {name} победил!"
                
                text = (f"⚔️ *Крестики-нолики*\n\n{res}\n\n"
                        f"❌ {session['player_x_name']}\n"
                        f"⭕ {session['player_o_name']}")
                
                if query.inline_message_id:
                    await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(board, game_over=True, multi=True))
                else:
                    await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(board, game_over=True, multi=True))
                
                if session_id in self.sessions: del self.sessions[session_id]
                return

            session["turn"] = O if session["turn"] == X else X
            next_name = session["player_x_name"] if session["turn"] == X else session["player_o_name"]
            text = (f"⚔️ *Крестики-нолики*\n\n"
                    f"Ход: {'❌' if session['turn'] == X else '⭕'} *{next_name}*\n\n"
                    f"❌ {session['player_x_name']}\n"
                    f"⭕ {session['player_o_name']}")
            
            if query.inline_message_id:
                await context.bot.edit_message_text(inline_message_id=session_id, text=text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(board, multi=True))
            else:
                await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(board, multi=True))
            return

        if data.startswith("ttt_move_"):
            idx = int(data.split("_")[2])
            session = self.sessions.get(session_id)
            if not session or session.get("game") != "ttt":
                await query.answer("Начни новую игру!", show_alert=True)
                return

            board = session["board"]
            board[idx] = X
            winner = self.check_winner(board)

            if not winner:
                bot_idx = self.bot_move(board)
                board[bot_idx] = O
                winner = self.check_winner(board)

            if winner:
                # Обновляем статистику в сессии пользователя
                user_stats = self.sessions.get(user_id, {})
                if winner == X:
                    user_stats["ttt_wins"] = user_stats.get("ttt_wins", 0) + 1
                    res_text = "🏆 *Ты победил!*"
                elif winner == O:
                    user_stats["ttt_losses"] = user_stats.get("ttt_losses", 0) + 1
                    res_text = "💀 *Бот победил!*"
                else:
                    user_stats["ttt_draws"] = user_stats.get("ttt_draws", 0) + 1
                    res_text = "🤝 *Ничья!*"
                
                self.sessions[user_id] = user_stats
                text = (f"⚔️ *Крестики-нолики*\n\n{res_text}\n\n"
                        f"📊 Счёт: 🏆{user_stats.get('ttt_wins', 0)} / 💀{user_stats.get('ttt_losses', 0)} / 🤝{user_stats.get('ttt_draws', 0)}")
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(board, game_over=True))
                if session_id in self.sessions: del self.sessions[session_id]
            else:
                text = (f"⚔️ *Крестики-нолики*\n\n"
                        f"Ты играешь за ❌, бот за ⭕\n"
                        f"📊 Счёт: 🏆{session['ttt_wins']} / 💀{session['ttt_losses']} / 🤝{session['ttt_draws']}\n\n"
                        f"Твой ход!")
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_board_keyboard(board))
            return

        if data.startswith("ttt_noop_"):
            await query.answer("Эта клетка уже занята!", show_alert=False)
