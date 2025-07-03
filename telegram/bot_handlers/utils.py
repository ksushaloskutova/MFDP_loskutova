from functools import wraps

import requests
from bot_instance import bot
from config import API_URL, logger
from telebot import types


def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["ℹ️ О проекте", "🔑 Войти", "📝 Регистрация", "🚪 Выход"]
    keyboard.add(*buttons)
    return keyboard


def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "Подробнее о возможностях", callback_data='features'
        ),
        types.InlineKeyboardButton("Техподдержка", url='https://t.me/your_support'),
    )
    return markup


def get_booking_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text="Записаться на диагностику", callback_data="time_slots"
    )
    btn2 = types.InlineKeyboardButton(
        text="Посмотреть текущую запись", callback_data="my_checkup_now"
    )
    btn3 = types.InlineKeyboardButton(
        text="Отправить снимок", callback_data="give_image"
    )
    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup


def get_task_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text="Получить результат и изображение", callback_data="get_task"
    )
    markup.add(btn1)
    return markup


def auth_required(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        try:
            if hasattr(message, 'message'):  # Для CallbackQuery
                message = message.message
            else:  # Для обычных Message
                message = message
            chat_id = message.chat.id

            chat_id = str(message.chat.id)
            logger.info(f"Starting auth check for chat_id: {chat_id}")

            response = requests.get(
                f"{API_URL}/user/token", params={"chat_id": chat_id}, timeout=5
            )

            logger.info(
                f"Auth check - ChatID: {chat_id}, Status: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0 and 'login' in data[0]:  # Если это список словарей
                        return func(message, login=data[0]['login'], *args, **kwargs)
                    else:
                        logger.error("Invalid data format: list without login field")
                        raise ValueError("Invalid response structure")
                elif isinstance(data, dict) and 'login' in data:  # Если это словарь
                    return func(message, login=data['login'], *args, **kwargs)
                else:
                    logger.error(f"Unexpected data format: {type(data)}")
                logger.info(f"User authorized: {data}")

            bot.send_message(chat_id, "❌ Пожалуйста, авторизуйтесь через /login")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {chat_id}: {str(e)}")
            bot.send_message(
                message.chat.id, "⚠️ Ошибка соединения с сервером авторизации"
            )
        except Exception as e:
            logger.error(f"Unexpected error for {chat_id}: {str(e)}", exc_info=True)
            bot.send_message(message.chat.id, "⚠️ Внутренняя ошибка сервера")

    return wrapped


def get_auth_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Авторизация", callback_data='start_login'))
    return markup
