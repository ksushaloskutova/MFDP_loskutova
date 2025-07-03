from bot_handlers.autntification import handle_logout, start_login, start_registration
from bot_handlers.utils import get_main_inline_keyboard, get_main_keyboard
from config import THERMO_CHECK_AI_INFO


def setup_menu_handlers(bot):
    @bot.message_handler(commands=['start', 'help'])
    def show_main_menu(message):
        bot.send_message(
            message.chat.id,
            f"Добро пожаловать, {message.from_user.first_name}!\nВыберите действие:",
            reply_markup=get_main_keyboard(),
        )
        bot.send_message(
            message.chat.id,
            "Дополнительные опции:",
            reply_markup=get_main_inline_keyboard(),
        )

    @bot.message_handler(
        func=lambda msg: msg.text
        in ["ℹ️ О проекте", "🔑 Войти", "📝 Регистрация", "🚪 Выход"]
    )
    def handle_reply_buttons(message):
        if message.text == "ℹ️ О проекте":
            bot.send_message(message.chat.id, THERMO_CHECK_AI_INFO)
        elif message.text == "🔑 Войти":
            start_login(message)
        elif message.text == "📝 Регистрация":
            start_registration(message)
        elif message.text == "🚪 Выход":
            handle_logout(message)

    @bot.callback_query_handler(func=lambda call: call.data == 'start_login')
    def handle_login_callback(call):
        # Создаем имитацию Message объекта из CallbackQuery
        message = call.message
        message.from_user = call.from_user
        message.text = call.data

        # Вызываем вашу функцию авторизации
        start_login(message)

        # Отправляем уведомление, что действие выполнено
        bot.answer_callback_query(call.id, "Авторизация")
