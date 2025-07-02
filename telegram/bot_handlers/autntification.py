import requests
from bot_handlers.utils import auth_required, get_booking_keyboard
from bot_instance import bot
from config import API_URL, logger


def start_registration(message):
    msg = bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(msg, process_email_step, msg.message_id)


def process_email_step(message, message_id):
    login = message.text
    bot.delete_message(message.chat.id, message_id)
    bot.delete_message(message.chat.id, message.message_id)
    msg = bot.send_message(message.chat.id, "Придумайте пароль:")
    bot.register_next_step_handler(msg, process_password_step, login, msg.message_id)


def process_password_step(message, login, message_id):
    password = message.text
    bot.delete_message(message.chat.id, message_id)
    bot.delete_message(message.chat.id, message.message_id)
    try:
        response = requests.post(
            f"{API_URL}/user/register",
            json={"login": login, "password": password},
            timeout=5,  # Добавляем таймаут
        )

        try:
            response_data = response.json()
        except ValueError:
            bot.send_message(message.chat.id, "❌ Не удалось обработать ответ сервера")
            return

        if response.status_code == 200:
            # Убираем register_next_step_handler и сразу показываем кнопку
            bot.send_message(
                message.chat.id,
                "✅ Регистрация успешна!\nАвторизуйтесь для дальнейших действий",
            )
        else:
            error_msg = response_data.get("detail", "Неизвестная ошибка")
            bot.send_message(message.chat.id, f"❌ Ошибка: {error_msg}")

    except requests.exceptions.Timeout:
        bot.send_message(message.chat.id, "❌ Сервер не отвечает, попробуйте позже")
    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"❌ Ошибка соединения: {str(e)}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Неожиданная ошибка")
        logger.error(f"Unexpected error: {str(e)}")


# Авторизация
def start_login(message):
    msg = bot.send_message(message.chat.id, "Введите ваш email:")
    bot.register_next_step_handler(msg, process_login_email_step, msg.message_id)


def process_login_email_step(message, message_id):
    login = message.text
    bot.delete_message(message.chat.id, message.message_id)
    bot.delete_message(message.chat.id, message_id)
    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(
        msg, process_login_password_step, login, msg.message_id
    )


def process_login_password_step(message, login, message_id):
    password = message.text
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, message_id)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    try:
        response = requests.post(
            f"{API_URL}/user/login",
            json={
                "login": login,
                "password": password,
                "chat_id": str(message.chat.id),
            },
        )
        response.raise_for_status()
        if response.status_code in (200, 299):
            # Успешная авторизация
            process_check_token(message)
        else:
            bot.send_message(message.chat.id, "❌ Ошибка авторизации:")
    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"❌ Ошибка авторизации: {str(e)}")


@auth_required
def process_check_token(message, login):
    try:
        # Создаем inline-клавиатуру
        markup = get_booking_keyboard()

        bot.send_message(
            message.chat.id,
            f"✅ Авторизация завершена! Добро пожаловать, {login}!\n"
            f"Используйте /help для списка команд",
            reply_markup=markup,
        )

    except Exception as e:
        logger.error(f"Error in process_check_token: {str(e)}")
        bot.send_message(
            message.chat.id, "⚠️ Произошла ошибка при завершении авторизации"
        )


# Выход
def handle_logout(message):
    try:
        chat_id = str(message.chat.id)
        # 2. Выполняем выход
        logout_response = requests.delete(
            f"{API_URL}/user/logout", params={"chat_id": chat_id}, timeout=5
        )

        if logout_response.status_code == 200:
            response_data = logout_response.json()
            status = response_data.get("status")
            if status == "success_logout":
                bot.send_message(chat_id, "✅ Вы успешно вышли из аккаунта.")
            if status == "success_not_login":
                bot.send_message(chat_id, "✅ Вы не были авторизованы.")
        else:
            # Пытаемся прочитать ошибку, если есть JSON
            try:
                error_msg = logout_response.json().get("detail", "Неизвестная ошибка")
            except ValueError:
                error_msg = logout_response.text or "Ошибка сервера"

            bot.send_message(chat_id, f"❌ Ошибка выхода: {error_msg}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Logout connection error: {str(e)}")
        bot.send_message(chat_id, "⚠️ Ошибка соединения с сервером")
    except Exception as e:
        logger.error(f"Unexpected logout error: {str(e)}", exc_info=True)
        bot.send_message(chat_id, "⚠️ Неожиданная ошибка при выходе")
