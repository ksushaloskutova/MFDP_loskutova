from bot_instance import bot
from apscheduler.schedulers.background import BackgroundScheduler
from bot_handlers.utils import get_task_keyboard
import functools

def init_scheduler_checkup(target_time, chat_id, info):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        functools.partial(bot.send_message, chat_id=chat_id, text=info),
        'date',
        run_date=target_time
    )
    scheduler.start()

def init_scheduler_get_task(target_time, chat_id, info):
    reply_markup = get_task_keyboard()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        functools.partial(bot.send_message, chat_id=chat_id, text=info, reply_markup=reply_markup),
        'date',
        run_date=target_time
    )
    scheduler.start()