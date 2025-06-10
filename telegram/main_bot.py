from bot_instance import bot
from config import logger
from bot_handlers.menu import setup_menu_handlers
from bot_handlers.time_to_checkup import setup_time_slots_handlers
from bot_handlers.checkup_history import check_my_checkup_records
from bot_handlers.ml_task import give_image_handlers

setup_menu_handlers(bot)
setup_time_slots_handlers(bot)
check_my_checkup_records(bot)
give_image_handlers(bot)


if __name__ == '__main__':
    logger.info("Starting bot...")
    bot.polling(non_stop=True)
    # Регистрация всех обработчиков
