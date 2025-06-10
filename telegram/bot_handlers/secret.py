from bot_handlers.utils import auth_required
from telebot import types
from bot_instance import bot


@bot.message_handler(commands=['secret'])
@auth_required
def private_command_handler(message: types.Message, login: str):
    bot.send_message(message.chat.id, f"✅ Доступ к приватной команде получен! Ваш логин: {login}")

