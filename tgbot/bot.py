import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, InlineQueryHandler
)
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto
from config import BOT_TOKEN

# Импорт игровых модулей
from games.tictactoe import TicTacToe
from games.rps import RPS
from games.battleship import Battleship
from games.casino import Casino
from games.minecraft import Minecraft
from games.drawing import Drawing
from games.guess import GuessNumber
from games.quiz import Quiz
from games.hangman import Hangman
from games.cities import Cities
from games.snake import Snake
from games.memes import MemeCreator, MEME_TEMPLATES

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище игровых сессий
game_sessions = {}

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚔️ Крестики-нолики", callback_data="game_ttt"),
         InlineKeyboardButton("✂️ Камень-ножницы-бумага", callback_data="game_rps")],
        [InlineKeyboardButton("🚢 Морской бой", callback_data="game_battleship"),
         InlineKeyboardButton("🎰 Казино (слоты)", callback_data="game_casino")],
        [InlineKeyboardButton("⛏️ Майнкрафт", callback_data="game_minecraft"),
         InlineKeyboardButton("🎨 Рисование (AI)", callback_data="game_drawing")],
        [InlineKeyboardButton("🔢 Угадай число", callback_data="game_guess"),
         InlineKeyboardButton("🧠 Викторина", callback_data="game_quiz")],
        [InlineKeyboardButton("🧩 Виселица", callback_data="game_hangman"),
         InlineKeyboardButton("🏙 Города", callback_data="game_cities")],
        [InlineKeyboardButton("🐍 Змейка", callback_data="game_snake"),
         InlineKeyboardButton("🎭 Мемы", callback_data="game_memes")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("🎮 Все игры"), KeyboardButton("🎨 Рисование")],
        [KeyboardButton("🎭 Создать мем"), KeyboardButton("⛏️ Майнкрафт")],
        [KeyboardButton("❓ Помощь"), KeyboardButton("🏠 Главная")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("menu", "Главное меню"),
        BotCommand("help", "Помощь"),
        BotCommand("guess", "Угадай число (в группе)"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"👋 Привет, *{user.first_name}*!\n\n"
            "🎮 Добро пожаловать в *Игровой бот*!\n\n"
            "Здесь ты можешь сыграть в 12 различных игр и функций.\n\n"
            "Выбери игру из списка ниже или используй кнопки меню внизу экрана:")
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_reply_keyboard())
    await update.message.reply_text("Выбери игру:", reply_markup=get_main_menu_keyboard())

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 *Главное меню* — выбери игру:", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("📖 *Помощь*\n\nКоманды:\n/start — запустить бота\n/menu — главное меню\n/help — помощь\n/guess — угадай число (в группе)\n\n"
            "Для игры в группах: добавь бота в группу и используй инлайн-режим (напиши @SmailGamesbot в чате).")
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await GuessNumber(game_sessions).start_group(update, context)

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.inline_query.query.lower().strip()
    results = []
    
    if not query_text:
        results = [
            InlineQueryResultArticle(id="ttt", title="⚔️ Крестики-нолики", input_message_content=InputTextMessageContent("⚔️ Вызываю на бой в *Крестики-нолики*!", parse_mode="Markdown"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Принять вызов", callback_data="game_ttt_multi")]])),
            InlineQueryResultArticle(id="rps", title="✂️ Камень-ножницы-бумага", input_message_content=InputTextMessageContent("✂️ Давай сыграем в *Камень-ножницы-бумага*!", parse_mode="Markdown"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Принять вызов", callback_data="game_rps_multi")]])),
            InlineQueryResultArticle(id="bs", title="🚢 Морской бой", input_message_content=InputTextMessageContent("🚢 Вызываю на бой в *Морской бой*!", parse_mode="Markdown"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Принять вызов", callback_data="game_bs_multi")]])),
            InlineQueryResultArticle(id="guess", title="🔢 Угадай число (Дуэль)", input_message_content=InputTextMessageContent("🔢 Давай играть в *Угадай число* (Дуэль)!", parse_mode="Markdown"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="game_guess_multi")]])),
            InlineQueryResultArticle(id="quiz", title="🧠 Викторина", input_message_content=InputTextMessageContent("🧠 Давай играть в *Викторину*!", parse_mode="Markdown"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="game_quiz")]]))
        ]
    elif query_text.startswith("мем") or query_text.startswith("meme"):
        parts = query_text.split(" ", 1)
        meme_text = parts[1] if len(parts) > 1 else ""
        top, bottom = (meme_text.split("|", 1) + [""])[:2] if "|" in meme_text else (meme_text, "")
        from games.memes import get_meme_url
        for i, tpl in enumerate(MEME_TEMPLATES):
            url = get_meme_url(tpl['id'], top.strip(), bottom.strip())
            results.append(InlineQueryResultPhoto(id=f"meme_{tpl['id']}_{i}", photo_url=url, thumbnail_url=url, caption=f"🎭 Мем: {tpl['name']}"))
    
    await update.inline_query.answer(results, cache_time=0)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.endswith("_multi"):
        game_type = data.split("_")[1]
        if game_type == "ttt": await TicTacToe(game_sessions).start_multiplayer(query, context)
        elif game_type == "rps": await RPS(game_sessions).start_multiplayer(query, context)
        elif game_type == "bs": await Battleship(game_sessions).start_multiplayer(query, context)
        elif game_type == "guess": await GuessNumber(game_sessions).start_multiplayer(query, context)
        return

    await query.answer()
    if data == "main_menu":
        text = "🎮 *Главное меню* — выбери игру:"
        if query.inline_message_id: await context.bot.edit_message_text(inline_message_id=query.inline_message_id, text=text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        else: await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        return

    if data == "game_ttt" or data.startswith("ttt_"): await TicTacToe(game_sessions).handle(query, context, data, user_id)
    elif data == "game_rps" or data.startswith("rps_"): await RPS(game_sessions).handle(query, context, data, user_id)
    elif data == "game_battleship" or data.startswith("bs_"): await Battleship(game_sessions).handle(query, context, data, user_id)
    elif data == "game_casino" or data.startswith("casino_"): await Casino(game_sessions).handle(query, context, data, user_id)
    elif data == "game_minecraft" or data.startswith("mc_"): await Minecraft(game_sessions).handle(query, context, data, user_id)
    elif data == "game_drawing" or data.startswith("draw_"): await Drawing(game_sessions).handle(query, context, data, user_id)
    elif data == "game_guess" or data.startswith("guess_"):
        guess = GuessNumber(game_sessions)
        if data == "game_guess": await guess.start(query, context, user_id)
        else: await guess.handle_callback(query, context, data, user_id)
    elif data == "game_quiz" or data.startswith("quiz_"):
        quiz = Quiz(game_sessions)
        if data == "game_quiz": await quiz.start(query, context, user_id)
        else: await quiz.handle(query, context, data, user_id)
    elif data == "game_hangman": await Hangman(game_sessions).start(query, context, user_id)
    elif data == "game_cities": await Cities(game_sessions).start(query, context, user_id)
    elif data == "game_snake" or data.startswith("snake_"):
        snake = Snake(game_sessions)
        if data == "game_snake": await snake.start(query, context, user_id)
        else: await snake.handle(query, context, data, user_id)
    elif data == "game_memes" or data.startswith("meme_"):
        memes = MemeCreator(game_sessions)
        if data == "game_memes": await memes.start(query, context, user_id)
        else: await memes.handle_callback(query, context, data, user_id)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Проверяем инлайн-сообщения (через reply_to_message)
    if update.message.reply_to_message and update.message.reply_to_message.via_bot:
        via_bot = update.message.reply_to_message.via_bot
        if via_bot.id == context.bot.id:
            # Это ответ на инлайн-сообщение нашего бота
            # Ищем активную инлайн-сессию
            for sid, sess in game_sessions.items():
                if sess.get("game") == "guess_duel" and sess.get("status") == "guessing":
                    await GuessNumber(game_sessions).handle_multi_input(update, context, text, user_id, sid)
                    return

    chat_id = update.effective_chat.id
    session = game_sessions.get(user_id, {})
    group_session = game_sessions.get(chat_id, {})

    # Обработка групповой игры «Угадай число»
    if group_session.get("game") == "guess_group":
        await GuessNumber(game_sessions).handle_input(update, context, text, chat_id)
        return

    if text == "🎮 Все игры": await menu_command(update, context); return
    elif text == "🎨 Рисование":
        drawing = Drawing(game_sessions)
        game_sessions[user_id] = {**session, "game": "drawing", "waiting_for_drawing": True}
        await update.message.reply_text("🎨 *Рисование (Бесплатный AI)*\n\nОпиши картинку:", parse_mode="Markdown", reply_markup=drawing.get_cancel_keyboard())
        return
    elif text == "🎭 Создать мем": await MemeCreator(game_sessions).start_from_text(update, context, user_id); return
    elif text == "⛏️ Майнкрафт":
        mc = Minecraft(game_sessions)
        game_sessions[user_id] = {**session, "game": "minecraft"}
        await update.message.reply_text(mc._main_text(game_sessions[user_id]), parse_mode="Markdown", reply_markup=mc.get_main_keyboard(user_id))
        return
    elif text == "❓ Помощь": await help_command(update, context); return
    elif text == "🏠 Главная": await start(update, context); return

    if session.get("waiting_for_drawing"): await Drawing(game_sessions).generate_image(update, context, text, user_id)
    elif session.get("waiting_for_guess"): await GuessNumber(game_sessions).handle_input(update, context, text, user_id)
    elif session.get("waiting_for_letter"): await Hangman(game_sessions).handle_input(update, context, text, user_id)
    elif session.get("waiting_for_city"): await Cities(game_sessions).handle_input(update, context, text, user_id)
    elif session.get("game") == "memes": await MemeCreator(game_sessions).handle_text(update, context, text, user_id)

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("guess", guess_command))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
