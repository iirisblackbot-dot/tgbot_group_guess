import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣", "🔔"]
WEIGHTS = [30, 25, 20, 15, 5, 3, 1, 1]

PAYOUTS = {
    "💎💎💎": 100, "7️⃣7️⃣7️⃣": 77, "⭐⭐⭐": 50, "🔔🔔🔔": 30,
    "🍇🍇🍇": 20, "🍊🍊🍊": 15, "🍋🍋🍋": 10, "🍒🍒🍒": 8, "🍒🍒": 3,
}

STARTING_COINS = 100

class Casino:
    def __init__(self, sessions):
        self.sessions = sessions

    def spin(self):
        return random.choices(SYMBOLS, weights=WEIGHTS, k=3)

    def calculate_win(self, reels, bet):
        combo = "".join(reels)
        if reels[0] == reels[1] == reels[2]:
            mult = PAYOUTS.get(combo, 5)
            return bet * mult, f"🎉 ДЖЕКПОТ! {combo} × {mult}"
        if reels.count("🍒") >= 2:
            return bet * 3, f"🍒 Два вишни × 3"
        if reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            return bet * 2, f"✨ Два одинаковых × 2"
        return 0, "😔 Нет выигрыша"

    def get_casino_keyboard(self, bet, user_id):
        keyboard = [
            [InlineKeyboardButton(f"🎰 КРУТИТЬ (ставка: {bet}🪙)", callback_data=f"casino_spin_{user_id}_{bet}")],
            [
                InlineKeyboardButton("5🪙", callback_data=f"casino_bet_{user_id}_5"),
                InlineKeyboardButton("10🪙", callback_data=f"casino_bet_{user_id}_10"),
                InlineKeyboardButton("25🪙", callback_data=f"casino_bet_{user_id}_25"),
                InlineKeyboardButton("50🪙", callback_data=f"casino_bet_{user_id}_50"),
            ],
            [
                InlineKeyboardButton("💰 Бонус", callback_data=f"casino_bonus_{user_id}"),
                InlineKeyboardButton("🏠 Меню", callback_data="main_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_casino_text(self, coins, bet, reels=None, result_text="", history=None):
        reels_str = " | ".join(reels) if reels else "❓ | ❓ | ❓"
        hist = "\n📜 *История:*\n" + "\n".join(history[-5:]) if history else ""
        return (f"🎰 *Казино — Слоты*\n\n"
                f"╔══════════════╗\n"
                f"║  {reels_str}  ║\n"
                f"╚══════════════╝\n\n"
                f"💰 Монеты: *{coins}*🪙\n"
                f"🎯 Ставка: *{bet}*🪙\n\n"
                f"{result_text}{hist}")

    async def handle(self, query, context, data, user_id):
        # В казино сессия всегда привязана к user_id для сохранения баланса
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "casino_coins": STARTING_COINS,
                "casino_bet": 10,
                "casino_history": [],
                "casino_last_bonus": 0
            }
        user_stats = self.sessions[user_id]
        coins = user_stats["casino_coins"]
        bet = user_stats["casino_bet"]
        history = user_stats["casino_history"]

        if data == "game_casino":
            text = self.get_casino_text(coins, bet, history=history, result_text="🎮 Выбери ставку и крути барабаны!\n\n")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_casino_keyboard(bet, user_id))
            return

        # Проверка владельца сессии в группе
        parts = data.split("_")
        if len(parts) > 2 and parts[2].isdigit():
            owner_id = int(parts[2])
            if user_id != owner_id:
                await query.answer("Это не твой игровой автомат! Начни свою игру в меню.", show_alert=True)
                return

        if data.startswith("casino_bet_"):
            new_bet = int(parts[3])
            if new_bet > coins:
                await query.answer(f"Недостаточно монет! У тебя {coins}🪙", show_alert=True)
                return
            user_stats["casino_bet"] = new_bet
            self.sessions[user_id] = user_stats
            text = self.get_casino_text(coins, new_bet, history=history, result_text=f"✅ Ставка изменена на {new_bet}🪙\n\n")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_casino_keyboard(new_bet, user_id))
            return

        if data.startswith("casino_spin_"):
            if coins < bet:
                await query.answer("Недостаточно монет! Получи бонус.", show_alert=True)
                return
            coins -= bet
            reels = self.spin()
            win_amount, result_msg = self.calculate_win(reels, bet)
            coins += win_amount
            hist_entry = f"{''.join(reels)} → {'+' if win_amount > 0 else '-'}{win_amount if win_amount > 0 else bet}🪙"
            history.append(hist_entry)
            user_stats.update({"casino_coins": coins, "casino_history": history})
            self.sessions[user_id] = user_stats
            result_text = f"{result_msg}\n" + (f"💵 Выигрыш: +{win_amount}🪙\n\n" if win_amount > 0 else "\n")
            text = self.get_casino_text(coins, bet, reels, result_text, history)
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_casino_keyboard(bet, user_id))
            return

        if data.startswith("casino_bonus_"):
            last_bonus = user_stats.get("casino_last_bonus", 0)
            now = int(time.time())
            if now - last_bonus < 3600:
                mins = (3600 - (now - last_bonus)) // 60
                await query.answer(f"Бонус можно получить через {mins} мин.", show_alert=True)
                return
            coins += 50
            user_stats.update({"casino_coins": coins, "casino_last_bonus": now})
            self.sessions[user_id] = user_stats
            text = self.get_casino_text(coins, bet, history=history, result_text=f"🎁 Получен бонус: +50🪙!\n\n")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_casino_keyboard(bet, user_id))
