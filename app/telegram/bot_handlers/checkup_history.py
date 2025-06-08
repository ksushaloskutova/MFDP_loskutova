import datetime
import requests
from app.telegram.config import API_URL, logger
from telebot import types
from datetime import datetime, timedelta
from app.telegram.bot_instance import bot
from .utils import auth_required, get_booking_keyboard

def check_my_checkup_records(bot_instance):
    @bot_instance.callback_query_handler(func=lambda call: call.data == 'my_checkup_now')
    @auth_required
    def handle_my_checkup_now(message, login):
        try:
            # Если это callback, отвечаем мгновенно
            if hasattr(message, "data"):  # Проверяем, что это callback
                bot_instance.answer_callback_query(message.id, "⌛ Запрос обрабатывается...")

            # Быстрый запрос к API (timeout=5 сек)
            response = requests.get(
                f"{API_URL}/checkup/last",
                params={"login": login},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                text = (f"✅ Последняя запись:\n"
                        f"Время: {data['checkup_time']}\n"
                        f"Место: {data['place']}\n"
                        f"Статус: {data['status']}")

            elif response.status_code == 404:
                text = "ℹ️ У вас нет активных записей."
            else:
                raise Exception(f"Ошибка API: {response.status_code}")
            # Отправка результата
            if hasattr(message, "message"):  # Если это callback, редактируем сообщение
                bot_instance.edit_message_text(
                    chat_id=message.message.chat.id,
                    message_id=message.message.message_id,
                    text=text,
                    reply_markup=get_booking_keyboard() if response.status_code == 404 else None
                )
            else:  # Если обычное сообщение
                bot_instance.send_message(
                    message.chat.id,
                    text,
                    reply_markup=get_booking_keyboard() if response.status_code == 404 else None
                )

        except requests.exceptions.Timeout:
            error_text = "⌛ Сервис не отвечает. Попробуйте позже."
            if hasattr(message, "message"):  # Callback
                bot_instance.edit_message_text(
                    chat_id=message.message.chat.id,
                    message_id=message.message.message_id,
                    text=error_text
                )
            else:  # Обычное сообщение
                bot_instance.send_message(message.chat.id, error_text)
        except Exception as e:
            logger.error(f"Checkup error: {str(e)}")
            error_text = "❌ Ошибка при обработке запроса"
            if hasattr(message, "message"):
                bot_instance.edit_message_text(
                    chat_id=message.message.chat.id,
                    message_id=message.message.message_id,
                    text=error_text
                )
            else:
                bot_instance.send_message(message.chat.id, error_text)