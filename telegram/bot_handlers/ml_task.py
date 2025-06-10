import requests
import logging
from telebot import types
from io import BytesIO
from PIL import Image
from config import API_URL, logger
from bot_handlers.sheduler import init_scheduler_get_task
from datetime import datetime, timedelta
import base64


def give_image_handlers(bot_instance):
    @bot_instance.callback_query_handler(func=lambda call: call.data == 'give_image')
    def give_image_button(call):
        try:
            chat_id = call.message.chat.id

            bot_instance.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=None
            )

            bot_instance.send_message(
                chat_id,
                "📷 Пожалуйста, отправьте изображение в формате JPEG/JPG\n"
                "Используйте /cancel для отмены"
            )

            # Регистрируем следующий шаг для получения изображения
            bot_instance.register_next_step_handler(call.message, process_received_image)

        except Exception as e:
            logger.error(f"Error in give_image_button: {e}")
            bot_instance.reply_to(
                call.message,
                "⚠️ Ошибка при обработке запроса. Попробуйте снова."
            )

    def process_received_image(message):
        try:
            chat_id = message.chat.id

            # Проверяем отмену операции
            if message.text and message.text.lower() == '/cancel':
                bot_instance.send_message(chat_id, "❌ Операция отменена.")
                return

            # Проверяем, что сообщение содержит изображение
            if not message.photo and not (message.document and
                                        message.document.mime_type in ['image/jpeg', 'image/jpg']):
                bot_instance.send_message(
                    chat_id,
                    "⚠️ Пожалуйста, отправьте изображение именно в формате JPEG/JPG\n"
                    "Либо как фото, либо как файл с расширением .jpg/.jpeg\n"
                    "Используйте /cancel для отмены"
                )
                bot_instance.register_next_step_handler(message, process_received_image)
                return

            # Получаем файл изображения
            if message.photo:
                file_info = bot_instance.get_file(message.photo[-1].file_id)
            else:
                file_info = bot_instance.get_file(message.document.file_id)

            downloaded_file = bot_instance.download_file(file_info.file_path)

            # Передаем изображение в функцию обработки
            process_and_send_image(message, downloaded_file)

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            bot_instance.send_message(
                chat_id,
                "⚠️ Ошибка при обработке изображения. Проверьте формат и попробуйте снова."
            )

    def process_and_send_image(message, image_bytes):
        try:
            chat_id = message.chat.id

            # Создаем временный файл для отправки
            with BytesIO(image_bytes) as file_bytes:
                files = {'file': ('image.jpg', file_bytes, 'image/jpeg')}

                # Отправляем уведомление о начале обработки
                bot_instance.send_message(chat_id, "🔄 Отправляю изображение на обработку...")

                # Отправка в ваш API
                response = requests.post(
                    f"{API_URL}/ml_task/",
                    files=files,
                    timeout=30
                )

                # Проверяем ответ
                response.raise_for_status()
                result = response.json()

                # Формируем ответ пользователю
                response_text = (
                    f"✅ Ваше изображение принято в обработку!\n\n"
                    f"🆔 ID задачи: {result.get('task_id', 'N/A')}\n"
                    f"🔑 Пароль: {result.get('password', 'N/A')}\n\n"
                    f"Используйте эти данные для проверки статуса."
                )

                bot_instance.send_message(chat_id, response_text)
                info = "Для получения изображения и результата напишите:"
                init_scheduler_get_task(datetime.now() + timedelta(minutes=1), chat_id, info)

        except requests.exceptions.RequestException as e:
            error_msg = f"⚠️ Ошибка при отправке изображения: {str(e)}"
            if isinstance(e, requests.exceptions.Timeout):
                error_msg = "⌛ Превышено время ожидания ответа сервера. Попробуйте позже."
            logger.error(f"API Error: {str(e)}")
            bot_instance.send_message(chat_id, error_msg)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            bot_instance.send_message(
                chat_id,
                "⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте снова."
            )

    @bot_instance.callback_query_handler(func=lambda call: call.data == 'get_task')
    def handle_get_task(call):
        try:
            chat_id = call.message.chat.id

            # Удаляем inline-клавиатуру
            bot_instance.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=None
            )

            # Запрашиваем ID задачи
            msg = bot_instance.send_message(
                chat_id,
                "Введите ID задачи:\n"
                "(Отправьте /cancel для отмены)"
            )

            # Регистрируем следующий шаг - обработку ID
            bot_instance.register_next_step_handler(msg, process_task_id)

        except Exception as e:
            logger.error(f"Error in handle_get_task: {e}")
            bot_instance.send_message(
                chat_id,
                "⚠️ Произошла ошибка. Пожалуйста, попробуйте снова."
            )

    def process_task_id(message):
        try:
            chat_id = message.chat.id

            # Проверяем отмену операции
            if message.text and message.text.lower() == '/cancel':
                bot_instance.send_message(chat_id, "❌ Операция отменена.")
                return

            task_id = message.text.strip()

            # Запрашиваем пароль
            msg = bot_instance.send_message(
                chat_id,
                "Введите пароль для задачи:\n"
                "(Отправьте /cancel для отмены)"
            )

            # Регистрируем следующий шаг - обработку пароля
            bot_instance.register_next_step_handler(msg, process_task_password, task_id)

        except Exception as e:
            logger.error(f"Error in process_task_id: {e}")
            bot_instance.send_message(
                chat_id,
                "⚠️ Ошибка при обработке ID задачи. Попробуйте снова."
            )

    def process_task_password(message, task_id):
        try:
            chat_id = message.chat.id
            # Проверяем отмену операции
            if message.text and message.text.lower() == '/cancel':
                bot_instance.send_message(chat_id, "❌ Операция отменена.")
                return

            password = message.text.strip()

            # Отправляем запрос к API
            bot_instance.send_message(chat_id, "🔄 Запрашиваю информацию о задаче...")

            response = requests.get(
                f"{API_URL}/ml_task/{task_id}",  # Подставляем переменную task_id
                params={'password': password},  # Пароль передается как query-параметр
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # Декодируем изображение
                image_bytes = base64.b64decode(data['image'])
                img = Image.open(BytesIO(image_bytes))

                # Сохраняем временно для отправки
                with BytesIO() as output:
                    img.save(output, format='JPEG')
                    output.seek(0)
                    # Отправляем изображение
                    bot_instance.send_photo(chat_id, photo=output)

                # Отправляем результат
                bot_instance.send_message(
                    chat_id,
                    f"📋 Результат задачи {task_id}:\n\n"
                    f"{data.get('result', 'Нет данных')}\n\n"
                )

            elif response.status_code == 404:
                bot_instance.send_message(chat_id, "❌ Задача не найдена")
            else:
                bot_instance.send_message(chat_id, f"⚠️ Ошибка: {response.text}")

        except Exception as e:
            logger.error(f"Error in process_task_id_for_result: {e}")
            bot_instance.send_message(chat_id, "⚠️ Ошибка при обработке запроса.")
        finally:
            # Очищаем временные данные
            bot_instance.delete_state(chat_id)