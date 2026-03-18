import aiohttp
import urllib.parse
import random
import io
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Drawing:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_drawing_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("🎨 Нарисовать снова", callback_data="game_drawing")],
            [InlineKeyboardButton("🏠 Меню", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_cancel_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle(self, query, context, data, user_id):
        if data == "game_drawing":
            self.sessions[user_id] = {
                **self.sessions.get(user_id, {}),
                "game": "drawing",
                "waiting_for_drawing": True,
            }
            text = (
                "🎨 *Рисование (Бесплатный AI)*\n\n"
                "Я использую бесплатный сервис *Pollinations.ai* для генерации изображений.\n\n"
                "Опиши картинку, которую хочешь нарисовать, и я создам её для тебя!\n\n"
                "Примеры:\n"
                "• _Закат над горами с озером_\n"
                "• _Космический корабль в стиле пиксель-арт_\n"
                "• _Уютный домик в лесу зимой_\n\n"
                "✏️ Напиши описание картинки:"
            )
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=self.get_cancel_keyboard()
            )
            return

    async def generate_image(self, update, context, prompt, user_id):
        session = self.sessions.get(user_id, {})
        session["waiting_for_drawing"] = False
        self.sessions[user_id] = session

        # Отправляем сообщение о генерации
        msg = await update.message.reply_text(
            f"🎨 *Рисую:* _{prompt}_\n\n⏳ Подождите, создаю изображение...",
            parse_mode="Markdown"
        )

        try:
            # Кодируем запрос для URL
            encoded_prompt = urllib.parse.quote(prompt)
            # Используем Pollinations.ai (бесплатно, без ключа)
            seed = random.randint(1, 1000000)
            # Используем модель flux и добавляем параметры для стабильности
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
            
            # Скачиваем изображение с таймаутом
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(image_url, timeout=45) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        
                        # Проверяем, что данные не пустые
                        if not image_data:
                            raise Exception("Получены пустые данные изображения")

                        # Отправляем изображение
                        photo_file = io.BytesIO(image_data)
                        photo_file.name = "drawing.png"
                        
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=f"🎨 *Готово!*\n\n📝 Запрос: _{prompt}_\n✨ Сгенерировано через Pollinations.ai",
                            parse_mode="Markdown",
                            reply_markup=self.get_drawing_keyboard()
                        )
                        # Удаляем сообщение "рисую..."
                        await msg.delete()
                    else:
                        raise Exception(f"Сервер ответил ошибкой: {resp.status}")

        except Exception as e:
            error_msg = str(e)
            await msg.edit_text(
                f"❌ *Ошибка генерации*\n\n"
                f"Не удалось создать изображение.\n"
                f"Попробуй другое описание или проверь подключение.\n\n"
                f"Ошибка: `{error_msg[:200]}`",
                parse_mode="Markdown",
                reply_markup=self.get_drawing_keyboard()
            )
