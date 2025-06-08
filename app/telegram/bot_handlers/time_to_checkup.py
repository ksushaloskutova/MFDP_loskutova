import datetime
import requests
from app.telegram.config import API_URL, logger
from telebot import types
from datetime import datetime, timedelta
from app.telegram.bot_instance import bot
from app.telegram.config import logger
from .utils import auth_required
from .sheduler import init_scheduler_checkup


def setup_time_slots_handlers(bot_instance):
    @bot_instance.callback_query_handler(func=lambda call: call.data == 'time_slots')
    def handle_time_slots_button(call):
        """Обработчик кнопки выбора временных слотов"""
        try:
            bot_instance.answer_callback_query(call.id)
            generate_week_buttons(bot_instance, call.message)
        except Exception as e:
            logger.error(f"Error in handle_time_slots_button: {e}")
            bot_instance.answer_callback_query(
                call.id,
                "Произошла ошибка при обработке запроса",
                show_alert=True
            )

    def generate_week_buttons(bot_instance, message):
        """Генерация кнопок с датами на неделю вперед"""
        try:
            start_date = datetime.now().date()
            keyboard = []

            for i in range(7):
                date = start_date + timedelta(days=i)
                button = types.InlineKeyboardButton(
                    text=date.strftime("%d.%m.%Y (%A)"),
                    callback_data=f"date_select:{date.strftime('%Y-%m-%d')}"
                )
                keyboard.append(button)

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*keyboard)

            bot_instance.send_message(
                message.chat.id,
                "Выберите дату:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Error in generate_week_buttons: {e}")
            bot_instance.send_message(
                message.chat.id,
                "Произошла ошибка при формировании списка дат"
            )

    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith("date_select:"))
    def handle_date_selection(call):
        """Обработчик выбора даты"""
        try:
            selected_date_str = call.data.split(":")[1]
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

            bot_instance.answer_callback_query(
                call.id,
                f"Выбрана дата: {selected_date.strftime('%d.%m.%Y')}"
            )

            # Удаляем предыдущее сообщение
            bot_instance.delete_message(call.message.chat.id, call.message.message_id)

            # Показываем временные блоки по 3 часа

            show_place_selection(bot_instance, call.message, selected_date)

        except Exception as e:
            logger.error(f"Error in handle_date_selection: {e}")
            bot_instance.answer_callback_query(
                call.id,
                "Ошибка при обработке выбранной даты",
                show_alert=True
            )

    def show_place_selection(bot_instance, message, selected_date):
        """Отображение выбора кабинета"""
        try:
            places = [1, 2, 3, 4, 5]  # Номера доступных кабинетов

            keyboard = [
                types.InlineKeyboardButton(
                    text=f"Кабинет {place}",
                    callback_data=f"place_select:{selected_date.strftime('%Y-%m-%d')}:{place}"
                )
                for place in places
            ]

            # Разбиваем на ряды по 2 кнопки
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*keyboard)

            bot_instance.send_message(
                message.chat.id,
                f"Выберите кабинет на {selected_date.strftime('%d.%m.%Y')}:",
                reply_markup=markup
            )

        except Exception as e:
            logger.error(f"Error in show_place_selection: {e}")
            bot_instance.send_message(
                message.chat.id,
                "Произошла ошибка при выборе кабинета"
            )

    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith("place_select:"))
    def handle_place_selection(call):
        """Обработчик выбора кабинета"""
        try:
            _, date_str, place = call.data.split(":")
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            bot_instance.answer_callback_query(
                call.id,
                f"Выбран кабинет: {place}"
            )

            # Удаляем предыдущее сообщение
            bot_instance.delete_message(call.message.chat.id, call.message.message_id)

            # Теперь показываем временные блоки для выбранной даты и кабинета
            show_time_blocks(bot_instance, call.message, selected_date, int(place))

        except Exception as e:
            logger.error(f"Error in handle_place_selection: {e}")
            bot_instance.answer_callback_query(
                call.id,
                "Ошибка при выборе кабинета",
                show_alert=True
            )

    def show_time_blocks(bot_instance, message, selected_date, place):
        """Отображение временных блоков по 3 часа"""
        try:
            time_blocks = [
                ("Утро (08:00-11:00)", 8),
                ("День (11:00-14:00)", 11),
                ("После обеда (14:00-17:00)", 14),
                ("Вечер (17:00-20:00)", 17)
            ]

            keyboard = [
                types.InlineKeyboardButton(
                    text=block[0],
                    callback_data=f"time_block:{place}:{selected_date.strftime('%Y-%m-%d')}:{block[1]}"
                )
                for block in time_blocks
            ]

            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(*keyboard)

            bot_instance.send_message(
                message.chat.id,
                f"Выберите временной блок на {selected_date.strftime('%d.%m.%Y')} (кабинет {place}):",
                reply_markup=markup
            )

        except Exception as e:
            logger.error(f"Error in show_time_blocks: {e}")
            bot_instance.send_message(
                message.chat.id,
                "Произошла ошибка при формировании временных блоков"
            )

    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith("time_block:"))
    def handle_time_block_selection(call):
        """Обработчик выбора временного блока"""
        try:
            _, place, date_str, start_hour = call.data.split(":")
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            bot_instance.answer_callback_query(
                call.id,
                f"Выбран блок с {start_hour}:00 (кабинет {place})"
            )

            # Удаляем сообщение с блоками
            bot_instance.delete_message(call.message.chat.id, call.message.message_id)

            # Передаем в функцию создания слотов
            available_time_for_checkup(bot_instance, call.message, selected_date, int(start_hour), int(place))
        except Exception as e:
            logger.error(f"Error in handle_time_block_selection: {e}")
            bot_instance.answer_callback_query(
                call.id,
                "Ошибка при обработке временного блока",
                show_alert=True
            )

    def available_time_for_checkup(bot_instance, message, date, start_hour, place):
        """Получение доступных слотов времени для записи через API"""
        try:
            # Преобразуем start_hour в целое число, если передано как строка "08:00"
            if isinstance(start_hour, str):
                start_h = int(start_hour.split(":")[0])
            else:
                start_h = start_hour

            end_h = start_h + 3  # Блок длится 3 часа

            # Делаем запрос к API
            response = requests.get(
                f"{API_URL}/checkup/time",
                params={
                    "date": date.strftime('%Y-%m-%d'),
                    "start_hour": start_h,
                    "end_hour": end_h,
                    "place": place
                },
                timeout=5
            )
            response.raise_for_status()

            if response.status_code == 200:
                time_slots = response.json()
                logger.info(f"time_slots{time_slots}")

                if not time_slots:
                    bot_instance.send_message(
                        message.chat.id,
                        f"На {date.strftime('%d.%m.%Y')} с {start_h:02d}:00 до {end_h:02d}:00 нет свободных слотов"
                    )
                    return

                # Создаем кнопки для доступных слотов
                keyboard = [
                    types.InlineKeyboardButton(
                        text=slot,
                        callback_data=f"final_slot/{place}/{date.strftime('%Y-%m-%d')}/{slot}"
                    )
                    for slot in time_slots
                ]

                # Разбиваем на ряды по 2 кнопки
                rows = [keyboard[i:i + 2] for i in range(0, len(keyboard), 2)]
                markup = types.InlineKeyboardMarkup(rows)

                # Удаляем предыдущее сообщение с выбором блока
                try:
                    bot_instance.delete_message(message.chat.id, message.message_id)
                except:
                    pass

                bot_instance.send_message(
                    message.chat.id,
                    f"Доступные слоты на {date.strftime('%d.%m.%Y')} с {start_h:02d}:00 до {end_h:02d}:00:",
                    reply_markup=markup
                )
            else:
                raise Exception(f"API вернул статус {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")

            # Fallback - создаем слоты вручную если API недоступно
            bot_instance.send_message(
                message.chat.id,
                "Сервер временно недоступен. Пожалуйста, попробуйте позже"
            )

        except Exception as e:
            logger.error(f"Error in available_time_for_checkup: {str(e)}")
            bot_instance.send_message(
                message.chat.id,
                "Произошла ошибка при получении доступного времени"
            )

    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith("final_slot/"))
    def handle_final_slot_selection(call):
        """Обработчик выбора конкретного слота"""
        try:
            logger.info(f"call.data{call.data}")
            _, place, date_str, time_slot = call.data.split("/")
            time_slot = time_slot.replace("-", ":")  # Возвращаем исходный формат (08-00-00 → 08:00:00)

            bot.answer_callback_query(call.id, f"Выбрано время: {time_slot}")
            msg = bot.send_message(call.message.chat.id, f"Для подтверждения записи на {date_str} {time_slot} {place}напишите: да")
            bot.register_next_step_handler(msg, complete_booking, date_str, time_slot, place)

        except Exception as e:
            logger.error(f"Error in handle_final_slot_selection: {e}")
            bot.answer_callback_query(call.id, "Ошибка при выборе слота", show_alert=True)

@auth_required
def complete_booking(message, date_str, time_slot, place, login):
    """Функция завершения записи с отправкой в API"""
    if message.text == "да":
        try:
            # Парсим дату и время
            booking_datetime = datetime.strptime(
                f"{date_str} {time_slot}",
                "%Y-%m-%d %H:%M:%S"
            )

            # Формируем запрос
            checkup_data = {
                "login" : login,  # или другой логин
                "checkup_time" : str(booking_datetime),
                "place" : place  # Укажите нужный place_id
            }

            # Отправляем в API
            response = requests.post(
                f"{API_URL}/checkup/new",
                json=checkup_data,
                timeout=5
            )
            logger.info(f"response.status_code{response.status_code}")
            if response.status_code == 200:
                bot.send_message(
                    message.chat.id,
                    f"✅ Запись успешно оформлена!\n"
                    f"📅 Дата: {date_str}\n"
                    f"⏰ Время: {time_slot}\n\n"
                    f"📅 Место: {place}\n\n"
                    f"Мы ждем вас в указанное время в указанном месте!"
                )
                booking_datetime = datetime.strptime(
                    f"{date_str} {time_slot}",
                    "%Y-%m-%d %H:%M:%S"
                )
                reminder_time = booking_datetime - timedelta(hours=2)
                info = f"Ваша запись уже через 2 часа: 📅 Дата: {date_str} ⏰ Время: {time_slot} 📅 Место: {place}"
                init_scheduler_checkup(reminder_time, message.chat.id, info)


            elif response.status_code == 409:  # Время занято
                error_msg = response.json().get("detail", "Это время уже занято")
                bot.send_message(
                    message.chat.id,
                    f"⏳ {error_msg}."
                )
            elif response.status_code == 403:  # Время занято
                error_msg = response.json().get("detail", "Запись невозможна")
                bot.send_message(
                    message.chat.id,
                    f"⏳ {error_msg}."
                )
            else:
                raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Error in complete_booking: {e}")
            bot.send_message(
                message.chat.id,
                "❌ Ошибка при сохранении записи. Попробуйте позже."
            )
    else:
        bot.send_message(message.chat.id, "Вы не записались.")