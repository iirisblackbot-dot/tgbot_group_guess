import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

RESOURCES = {
    "wood": {"name": "🪵 Дерево", "emoji": "🪵"},
    "stone": {"name": "🪨 Камень", "emoji": "🪨"},
    "coal": {"name": "⚫ Уголь", "emoji": "⚫"},
    "iron": {"name": "🔩 Железо", "emoji": "🔩"},
    "gold": {"name": "🟡 Золото", "emoji": "🟡"},
    "diamond": {"name": "💎 Алмаз", "emoji": "💎"},
    "food": {"name": "🍖 Еда", "emoji": "🍖"},
}

CRAFTS = {
    "wooden_pickaxe": {"name": "⛏️ Деревянная кирка", "recipe": {"wood": 3}, "desc": "Позволяет добывать камень и уголь быстрее"},
    "stone_pickaxe": {"name": "⛏️ Каменная кирка", "recipe": {"wood": 2, "stone": 3}, "desc": "Позволяет добывать железо"},
    "iron_pickaxe": {"name": "⛏️ Железная кирка", "recipe": {"wood": 2, "iron": 3}, "desc": "Позволяет добывать золото и алмазы"},
    "torch": {"name": "🕯️ Факел", "recipe": {"coal": 1, "wood": 1}, "desc": "Освещает шахту"},
    "sword": {"name": "⚔️ Меч", "recipe": {"wood": 1, "iron": 2}, "desc": "Для защиты от мобов"},
    "house": {"name": "🏠 Дом", "recipe": {"wood": 10, "stone": 15}, "desc": "Твой дом в мире Майнкрафт!"},
    "furnace": {"name": "🔥 Печь", "recipe": {"stone": 8}, "desc": "Для переплавки руды"},
    "chest": {"name": "📦 Сундук", "recipe": {"wood": 8}, "desc": "Хранилище ресурсов"},
}

MINE_TABLE = {
    "surface": {"wood": (3, 8), "food": (1, 3)},
    "cave": {"stone": (2, 6), "coal": (1, 4), "iron": (0, 2)},
    "deep": {"stone": (1, 3), "coal": (1, 3), "iron": (1, 3), "gold": (0, 2), "diamond": (0, 1)}
}

def new_mc_session():
    return {
        "game": "minecraft",
        "inventory": {r: 0 for r in RESOURCES},
        "crafted": [],
        "health": 20,
        "level": 1,
        "xp": 0,
        "day": 1,
        "pickaxe": "none",
    }

class Minecraft:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_inventory_text(self, session):
        inv = session["inventory"]
        lines = [f"{RESOURCES[k]['emoji']} {RESOURCES[k]['name']}: {inv[k]}" for k in RESOURCES if inv.get(k, 0) > 0]
        return "\n".join(lines) if lines else "Инвентарь пуст"

    def get_crafted_text(self, session):
        crafted = session.get("crafted", [])
        return ", ".join([CRAFTS[k]["name"] for k in crafted if k in CRAFTS]) if crafted else "Ничего не скрафчено"

    def get_main_keyboard(self, user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌲 Рубить лес", callback_data=f"mc_mine_{user_id}_surface"),
             InlineKeyboardButton("⛏️ Добывать в пещере", callback_data=f"mc_mine_{user_id}_cave")],
            [InlineKeyboardButton("💎 Глубокая шахта", callback_data=f"mc_mine_{user_id}_deep"),
             InlineKeyboardButton("🔨 Крафт", callback_data=f"mc_craft_menu_{user_id}")],
            [InlineKeyboardButton("🎒 Инвентарь", callback_data=f"mc_inventory_{user_id}"),
             InlineKeyboardButton("📊 Статус", callback_data=f"mc_status_{user_id}")],
            [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
        ])

    def get_craft_keyboard(self, session, user_id):
        inv = session["inventory"]
        keyboard = []
        row = []
        for key, craft in CRAFTS.items():
            can_craft = all(inv.get(r, 0) >= amt for r, amt in craft["recipe"].items())
            already = key in session.get("crafted", [])
            emoji = "✅" if already else ("🔨" if can_craft else "🔒")
            row.append(InlineKeyboardButton(f"{emoji} {craft['name']}", callback_data=f"mc_craft_{user_id}_{key}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"mc_back_{user_id}")])
        return InlineKeyboardMarkup(keyboard)

    async def handle(self, query, context, data, user_id):
        # В майнкрафте сессия всегда привязана к user_id
        user_stats = self.sessions.get(user_id, {})
        if user_stats.get("game") != "minecraft":
            user_stats = new_mc_session()
            self.sessions[user_id] = user_stats

        # Проверка владельца сессии в группе
        parts = data.split("_")
        if len(parts) > 2 and parts[2].isdigit():
            owner_id = int(parts[2])
            if user_id != owner_id:
                await query.answer("Это не твой мир! Начни свою игру в меню.", show_alert=True)
                return

        if data == "game_minecraft" or data.startswith("mc_back_"):
            text = self._main_text(user_stats)
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_main_keyboard(user_id))
            return

        if data.startswith("mc_mine_"):
            zone = parts[3]
            zone_names = {"surface": "🌲 Лес", "cave": "⛏️ Пещера", "deep": "💎 Глубокая шахта"}
            if zone == "cave" and user_stats.get("pickaxe", "none") == "none":
                await query.answer("Нужна кирка для добычи в пещере!", show_alert=True)
                return
            if zone == "deep" and user_stats.get("pickaxe", "none") not in ["stone", "iron"]:
                await query.answer("Нужна каменная или железная кирка!", show_alert=True)
                return

            gained, xp, event = self._mine_resources(user_stats, zone)
            self.sessions[user_id] = user_stats
            gained_text = "\n".join([f"+{v} {RESOURCES[k]['emoji']} {RESOURCES[k]['name']}" for k, v in gained.items()]) or "Ничего не нашёл..."
            text = (f"⛏️ *Майнкрафт — Добыча*\n\n📍 Зона: {zone_names[zone]}\n\n*Добыто:*\n{gained_text}\n"
                    f"✨ +{xp} XP{event}\n\n❤️ Здоровье: {user_stats['health']}/20\n⭐ Уровень: {user_stats['level']}")
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⛏️ Добыть ещё", callback_data=data),
                                              InlineKeyboardButton("⬅️ Назад", callback_data=f"mc_back_{user_id}")]])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            return

        if data.startswith("mc_craft_menu_"):
            text = (f"🔨 *Майнкрафт — Крафт*\n\n*Инвентарь:*\n{self.get_inventory_text(user_stats)}\n\n"
                    f"🔨 — можно скрафтить | 🔒 — не хватает | ✅ — уже есть")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_craft_keyboard(user_stats, user_id))
            return

        if data.startswith("mc_craft_"):
            item_key = parts[3]
            craft = CRAFTS[item_key]
            inv = user_stats["inventory"]
            for res, amt in craft["recipe"].items():
                if inv.get(res, 0) < amt:
                    await query.answer(f"Не хватает ресурсов!", show_alert=True)
                    return
            for res, amt in craft["recipe"].items(): user_stats["inventory"][res] -= amt
            if item_key not in user_stats.get("crafted", []): user_stats.setdefault("crafted", []).append(item_key)
            if "pickaxe" in item_key: user_stats["pickaxe"] = item_key.split("_")[0]
            self.sessions[user_id] = user_stats
            text = (f"🔨 *Скрафчено: {craft['name']}*\n\n📝 {craft['desc']}\n\n*Инвентарь:*\n{self.get_inventory_text(user_stats)}")
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔨 Крафт ещё", callback_data=f"mc_craft_menu_{user_id}"),
                                              InlineKeyboardButton("⬅️ Назад", callback_data=f"mc_back_{user_id}")]])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            return

        if data.startswith("mc_inventory_"):
            text = (f"🎒 *Инвентарь*\n\n{self.get_inventory_text(user_stats)}\n\n🛠️ *Скрафчено:*\n{self.get_crafted_text(user_stats)}")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f"mc_back_{user_id}")]]))
            return

        if data.startswith("mc_status_"):
            text = (f"📊 *Статус*\n\n❤️ Здоровье: {user_stats['health']}/20\n⭐ Уровень: {user_stats['level']}\n"
                    f"⛏️ Кирка: {user_stats.get('pickaxe','none')}\n\n🎒 *Инвентарь:*\n{self.get_inventory_text(user_stats)}")
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f"mc_back_{user_id}")]]))
            return

    def _mine_resources(self, session, zone):
        table = MINE_TABLE.get(zone, MINE_TABLE["surface"])
        pickaxe = session.get("pickaxe", "none")
        gained = {}
        for res, (min_v, max_v) in table.items():
            bonus = 1 if (pickaxe == "wooden" and res in ["stone", "coal"]) or (pickaxe == "stone" and res in ["iron", "coal"]) or (pickaxe == "iron" and res in ["gold", "diamond"]) else 0
            amount = random.randint(min_v, max_v + bonus)
            if amount > 0:
                session["inventory"][res] = session["inventory"].get(res, 0) + amount
                gained[res] = amount
        xp = random.randint(5, 15)
        session["xp"] += xp
        if session["xp"] >= session["level"] * 100:
            session["level"] += 1
            session["xp"] = 0
        event = ""
        if zone == "deep" and random.random() < 0.2:
            dmg = random.randint(2, 5)
            session["health"] = max(0, session["health"] - dmg)
            event = f"\n⚠️ Атака моба! -{dmg}❤️"
            if session["health"] <= 0:
                session["health"] = 10
                event += "\n💀 Ты погиб! Возрождение."
        return gained, xp, event

    def _main_text(self, session):
        return (f"⛏️ *Майнкрафт*\n\n❤️ Здоровье: {session['health']}/20\n⭐ Уровень: {session['level']}\n"
                f"⛏️ Кирка: {session.get('pickaxe','none')}\n\nДобывай ресурсы и развивайся!")
