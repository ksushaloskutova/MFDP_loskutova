from bot_instance import bot
from apscheduler.schedulers.background import BackgroundScheduler
import functools

def init_scheduler_checkup(target_time, chat_id, info):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        functools.partial(bot.send_message, chat_id=chat_id, text=info),
        'date',
        run_date=target_time
    )
    scheduler.start()
