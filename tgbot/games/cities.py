import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CITIES = ["МОСКВА", "АСТРАХАНЬ", "НОВОСИБИРСК", "КАЗАНЬ", "НИЖНИЙ НОВГОРОД", "ОМСК", "САМАРА", "РОСТОВ-НА-ДОНУ", "УФА", "КРАСНОЯРСК", "ПЕРМЬ", "ВОРОНЕЖ", "ВОЛГОГРАД", "КРАСНОДАР", "САРАТОВ", "ТЮМЕНЬ", "ТОЛЬЯТТИ", "ИЖЕВСК", "БАРНАУЛ", "УЛЬЯНОВСК", "ИРКУТСК", "ХАБАРОВСК", "ЯРОСЛАВЛЬ", "ВЛАДИВОСТОК", "МАХАЧКАЛА", "ТОМСК", "ОРЕНБУРГ", "КЕМЕРОВО", "НОВОКУЗНЕЦК", "РЯЗАНЬ", "НАБЕРЕЖНЫЕ ЧЕЛНЫ", "ПЕНЗА", "ЛИПЕЦК", "КИРОВ", "ЧЕБОКСАРЫ", "ТУЛА", "КАЛИНИНГРАД", "КУРСК", "УЛАН-УДЭ", "СТАВРОПОЛЬ", "МАГНИТОГОРСК", "ТВЕРЬ", "ИВАНОВО", "БРЯНСК", "СОЧИ", "БЕЛГОРОД", "СУРГУТ", "ВЛАДИМИР", "АРХАНГЕЛЬСК", "ЧИТА", "КАЛУГА", "СМОЛЕНСК", "ВОЛЖСКИЙ", "КУРГАН", "ОРЕЛ", "ЧЕРЕПОВЕЦ", "ВОЛОГДА", "САРАНСК", "ВЛАДИКАВКАЗ", "ЯКУТСК", "МУРМАНСК", "ПОДОЛЬСК", "ТАМБОВ", "ГРОЗНЫЙ", "СТЕРЛИТАМАК", "КОСТРОМА", "ПЕТРОЗАВОДСК", "НИЖНЕВАРТОВСК", "ЙОШКАР-ОЛА", "НОВОРОССИЙСК", "БАЛАШИХА", "ТАГАНРОГ", "КОМСОМОЛЬСК-НА-АМУРЕ", "СЫКТЫВКАР", "НАЛЬЧИК", "ШАХТЫ", "БРАТСК", "ДЗЕРЖИНСК", "ОРСК", "АНГАРСК", "БЛАГОВЕЩЕНСК", "ЭНГЕЛЬС", "СТАРЫЙ ОСКОЛ", "ВЕЛИКИЙ НОВГОРОД", "КОРОЛЕВ", "ПСКОВ", "БИЙСК", "ПРОКОПЬЕВСК", "БАЛАКОВО", "РЫБИНСК", "ЮЖНО-САХАЛИНСК", "АРМАВИР", "ЛЮБЕРЦЫ", "МЫТИЩИ", "СЕВЕРОДВИНСК", "ПЕТРОПАВЛОВСК-КАМЧАТСКИЙ", "АБАКАН", "НОРИЛЬСК", "СЫЗРАНЬ", "ВОЛГОДОНСК", "НОВОЧЕРКАССК", "КАМЕНСК-УРАЛЬСКИЙ", "ЗЛАТОУСТ", "АЛЬМЕТЬЕВСК", "ЭЛЕКТРОСТАЛЬ", "КЕРЧЬ", "МИАСС", "САЛАВАТ", "ХАСАВЮРТ", "ПЯТИГОРСК", "КОПЕЙСК", "НАХОДКА", "РУБЦОВСК", "МАЙКОП", "КОЛОМНА", "БЕРЕЗНИКИ", "ОДИНЦОВО", "ДОМОДЕДОВО", "КОВРОВ", "НЕФТЕКАМСК", "КАСПИЙСК", "НЕФТЕЮГАНСК", "КИСЛОВОДСК", "НОВОЧЕБОКСАРСК", "БАТАЙСК", "ЩЕЛКОВО", "ДЕРБЕНТ", "НЕВИННОМЫССК", "КЫЗЫЛ", "СЕРПУХОВ", "ОКТЯБРЬСКИЙ", "РАМЕНСКОЕ", "ЧЕРКЕССК", "НОВОМОСКОВСК", "ПЕРВОУРАЛЬСК", "ОРЕХОВО-ЗУЕВО", "ДИМИТРОВГРАД", "ВИДНОЕ", "КАМЫШИН", "МУРОМ", "ОБНИНСК", "НОВЫЙ УРЕНГОЙ", "КРАСНОГОРСК", "ПУШКИНО", "ЖУКОВСКИЙ", "АРТЕМ", "СЕВЕРСК", "ЕЙСК", "АРЗАМАС", "БЕРДСК", "ЭЛИСТА", "НОГИНСК", "ЖЕЛЕЗНОГОРСК"]

class Cities:
    def __init__(self, sessions):
        self.sessions = sessions

    async def start(self, query, context, user_id):
        self.sessions[user_id] = {
            "game": "cities",
            "used": [],
            "last_letter": None,
            "waiting_for_city": True,
            "chat_id": query.message.chat_id if query.message else None
        }
        text = (
            "🏙 *Города*\n\n"
            "Правила: называй город, я назову город на последнюю букву твоего.\n"
            "Буквы 'Ь', 'Ы', 'Ъ' пропускаются.\n\n"
            "Напиши название любого города!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]))

    async def handle_input(self, update, context, text, user_id):
        session = self.sessions.get(user_id)
        if not session or session.get("game") != "cities" or not session.get("waiting_for_city"):
            return

        city = text.upper().strip()
        if city in session["used"]:
            await update.message.reply_text(f"❌ Город *{city}* уже был!")
            return

        if session["last_letter"] and city[0] != session["last_letter"]:
            await update.message.reply_text(f"❌ Город должен начинаться на букву *{session['last_letter']}*!")
            return

        session["used"].append(city)
        last_char = self._get_last_letter(city)
        
        bot_city = self._find_city(last_char, session["used"])
        if not bot_city:
            session["waiting_for_city"] = False
            await update.message.reply_text(f"🎉 *Я сдаюсь!* Ты победил! Я не знаю городов на букву *{last_char}*.", parse_mode="Markdown", reply_markup=self._get_finish_keyboard())
            return

        session["used"].append(bot_city)
        next_letter = self._get_last_letter(bot_city)
        session["last_letter"] = next_letter

        text = (f"🏙 *Города*\n\nТы: *{city}*\nЯ: *{bot_city}*\n\nТвой ход на букву *{next_letter}*!")
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]))

    def _get_last_letter(self, city):
        for char in reversed(city):
            if char not in ["Ь", "Ы", "Ъ"]:
                return char
        return city[-1]

    def _find_city(self, letter, used):
        available = [c for c in CITIES if c.startswith(letter) and c not in used]
        if available:
            return random.choice(available)
        return None

    def _get_finish_keyboard(self):
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Играть снова", callback_data="game_cities"),
                                      InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
