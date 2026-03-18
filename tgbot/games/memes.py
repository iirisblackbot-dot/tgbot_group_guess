import aiohttp
import urllib.parse
import io
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# memegen.link сопоставление ID (проверенные ID для memegen.link)
MEMEGEN_IDS = {
    "181913649": "drake",
    "87743020": "buttons",
    "112126428": "boyfriend",
    "131087935": "balloon",
    "217743513": "woman-yelling-at-cat",
    "43868911": "batman",
    "124053312": "change-my-mind",
    "102156234": "spongebob",
    "91538330": "buzz",
    "61579": "simply",
}

def get_meme_url(tpl_id, top, bottom):
    def clean_text(t):
        if not t: return "_"
        # memegen.link требует специфического экранирования
        # Заменяем пробелы на _, спецсимволы на их коды
        return t.replace("-", "--").replace("_", "__").replace(" ", "_").replace("?", "~q").replace("%", "~p").replace("#", "~h").replace("/", "~s").replace('"', "''")
    
    m_id = MEMEGEN_IDS.get(tpl_id, tpl_id) # Если нет в словаре, пробуем использовать как есть
    safe_top = clean_text(top)
    safe_bottom = clean_text(bottom)
    return f"https://api.memegen.link/images/{m_id}/{urllib.parse.quote(safe_top)}/{urllib.parse.quote(safe_bottom)}.png"

# Популярные шаблоны мемов
MEME_TEMPLATES = [
    {"id": "drake", "name": "Drake Hotline Bling", "emoji": "🕺"},
    {"id": "buttons", "name": "Two Buttons", "emoji": "🔘"},
    {"id": "boyfriend", "name": "Distracted Boyfriend", "emoji": "👫"},
    {"id": "balloon", "name": "Running Away Balloon", "emoji": "🎈"},
    {"id": "woman-yelling-at-cat", "name": "Woman Yelling at a Cat", "emoji": "🐱"},
    {"id": "batman", "name": "Batman Slapping Robin", "emoji": "🦇"},
    {"id": "change-my-mind", "name": "Change My Mind", "emoji": "☕"},
    {"id": "spongebob", "name": "Mocking Spongebob", "emoji": "🧽"},
    {"id": "buzz", "name": "X, X Everywhere", "emoji": "🌎"},
    {"id": "simply", "name": "One Does Not Simply", "emoji": "💍"},
]

class MemeCreator:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_template_keyboard(self):
        keyboard = []
        for i in range(0, len(MEME_TEMPLATES), 2):
            row = [
                InlineKeyboardButton(f"{MEME_TEMPLATES[i]['emoji']} {MEME_TEMPLATES[i]['name']}", 
                                     callback_data=f"meme_tpl_{MEME_TEMPLATES[i]['id']}")
            ]
            if i + 1 < len(MEME_TEMPLATES):
                row.append(InlineKeyboardButton(f"{MEME_TEMPLATES[i+1]['emoji']} {MEME_TEMPLATES[i+1]['name']}", 
                                               callback_data=f"meme_tpl_{MEME_TEMPLATES[i+1]['id']}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    async def start(self, query, context, user_id):
        self.sessions[user_id] = {
            "game": "memes",
            "phase": "choosing_template"
        }
        text = "🎭 *Создание мемов*\n\nВыбери шаблон для своего мема:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=self.get_template_keyboard())

    async def start_from_text(self, update, context, user_id):
        self.sessions[user_id] = {
            "game": "memes",
            "phase": "choosing_template"
        }
        text = "🎭 *Создание мемов*\n\nВыбери шаблон для своего мема:"
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=self.get_template_keyboard())

    async def handle_callback(self, query, context, data, user_id):
        session = self.sessions.get(user_id)
        if not session or session.get("game") != "memes":
            return

        if data.startswith("meme_tpl_"):
            template_id = data.replace("meme_tpl_", "")
            session["template_id"] = template_id
            session["phase"] = "waiting_top_text"
            
            await query.edit_message_text(
                "📝 *Шаблон выбран!*\n\nТеперь напиши текст для **верхней** части мема (или отправь '-', чтобы оставить пустым):",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]])
            )

    async def handle_text(self, update, context, text, user_id):
        session = self.sessions.get(user_id)
        if not session or session.get("game") != "memes":
            return

        if session["phase"] == "waiting_top_text":
            session["top_text"] = "" if text == "-" else text
            session["phase"] = "waiting_bottom_text"
            await update.message.reply_text(
                "✅ Верхний текст принят!\n\nТеперь напиши текст для **нижней** части мема (или '-', чтобы оставить пустым):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]])
            )
            
        elif session["phase"] == "waiting_bottom_text":
            session["bottom_text"] = "" if text == "-" else text
            session["phase"] = "generating"
            
            status_msg = await update.message.reply_text("⏳ *Создаю ваш мем...* Пожалуйста, подождите.", parse_mode="Markdown")
            
            try:
                top = session["top_text"]
                bottom = session["bottom_text"]
                tpl_id = session["template_id"]
                
                meme_url = get_meme_url(tpl_id, top, bottom)
                
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.get(meme_url, timeout=15) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            photo_file = io.BytesIO(image_data)
                            photo_file.name = "meme.png"
                            
                            await update.message.reply_photo(
                                photo=photo_file,
                                caption="🎭 *Ваш мем готов!*",
                                parse_mode="Markdown",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("🔄 Создать еще", callback_data="game_memes")],
                                    [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
                                ])
                            )
                            await status_msg.delete()
                        else:
                            # Если 404, пробуем альтернативный шаблон (drake)
                            if resp.status == 404 and tpl_id != "drake":
                                alt_url = get_meme_url("drake", top, bottom)
                                async with http_session.get(alt_url, timeout=10) as alt_resp:
                                    if alt_resp.status == 200:
                                        image_data = await alt_resp.read()
                                        photo_file = io.BytesIO(image_data)
                                        photo_file.name = "meme.png"
                                        await update.message.reply_photo(
                                            photo=photo_file,
                                            caption="🎭 *Ваш мем готов!* (Использован запасной шаблон)",
                                            parse_mode="Markdown",
                                            reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton("🔄 Создать еще", callback_data="game_memes")],
                                                [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]
                                            ])
                                        )
                                        await status_msg.delete()
                                        return
                            
                            raise Exception(f"Сервер мемов ответил ошибкой: {resp.status}")
                
                session["phase"] = "finished"
                
            except Exception as e:
                await status_msg.edit_text(f"❌ *Ошибка при создании мема:* {str(e)}\nПопробуйте еще раз позже.", parse_mode="Markdown")
                session["phase"] = "finished"
