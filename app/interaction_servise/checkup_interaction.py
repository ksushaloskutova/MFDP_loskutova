from object_servise.checkup import Checkup, CheckupResponse
from typing import List, Optional, Dict
from datetime import date, time, timedelta
import datetime
from sqlalchemy import and_, func
from collections import defaultdict
from config import logger

def get_all_checkup(session) -> List[Checkup]:
    return session.query(Checkup).all()

def get_all_checkup_by_time_place(session, target_date: date, hour_range: tuple[int, int], place: int) -> Optional[List[
    Checkup]]:
    start_hour, end_hour = hour_range

    # Если end_hour превышает 23, то устанавливаем его на 23
    if end_hour > 23:
        end_hour = 23

    # Определяем начальный и конечный datetime
    start_datetime = datetime.datetime.combine(target_date, time(start_hour))
    end_datetime = datetime.datetime.combine(target_date, time(end_hour, 0, 0)) + timedelta(seconds=59)

    return session.query(Checkup).filter(
        and_(
            Checkup.checkup_time >= start_datetime,
            Checkup.checkup_time <= end_datetime,
            Checkup.status == 'record',
            Checkup.place == place
        )
    ).all()


def get_available_time_slots(
        session,
        target_date: date,
        hour_range: tuple[int, int],
        place: int,
        procedure_duration: timedelta = timedelta(minutes=15)
) -> List[time]:
    """Возвращает доступные временные слоты для записи"""
    # Получаем все занятые записи
    booked_checkups = get_all_checkup_by_time_place(session, target_date, hour_range, place)
    logger.info(f"get_all_checkup_by_time: {booked_checkups}")
    # Создаем множество занятых слотов
    booked_slots = set()
    for checkup in booked_checkups:
        start_time = checkup.checkup_time.time()
        end_time = (datetime.datetime.combine(date.min, start_time) + procedure_duration).time()

        current_time = start_time
        while current_time < end_time:
            booked_slots.add(current_time)
            current_time = (datetime.datetime.combine(date.min, current_time) + timedelta(minutes=15)).time()

    # Генерируем все возможные слоты
    start_hour, end_hour = hour_range
    all_slots = []
    current_time = time(start_hour, 0)
    end_time = time(end_hour, 45)

    while current_time <= end_time:
        all_slots.append(current_time)
        current_time = (datetime.datetime.combine(date.min, current_time) + timedelta(minutes=15)).time()

    logger.info(f"all slots:{all_slots}")
    # Фильтруем свободные слоты
    free_slots = [slot for slot in all_slots if slot not in booked_slots]

    return free_slots

def get_last_checkup(session) -> Optional[Checkup]:
    return session.query(Checkup).order_by(Checkup.id.desc()).first()

def get_checkup_by_login(login: str, session) -> Optional[List[Checkup]]:
    checkups = session.query(Checkup).filter(Checkup.login == login).all()
    return checkups if checkups else None


from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.exc import SQLAlchemyError
from typing import Optional


def get_checkup_last_by_login(login: str, session) -> Optional[dict]:
    try:
        # Используем ORM вместо raw SQL
        checkup = (
            session.query(Checkup)
            ).filter(
                Checkup.login == login,
                Checkup.status.in_(["record", "finished"])
            ).order_by(
                Checkup.id.desc()
            ).first()
        if not checkup:
            return {"result": "not_checkups"}
        return {"result": checkup}

    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД: {str(e)}", exc_info=True)
        session.rollback()
        return None
    except Exception as e:
        logger.critical(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        return None


def write_checkup(new_checkup: Checkup, session) -> None:
    session.add(new_checkup)
    session.commit()
    session.refresh(new_checkup)

def check_time_available(time_to_check: datetime.datetime, place: int, session):
    existing = session.query(Checkup).filter(
        Checkup.checkup_time == time_to_check,
        Checkup.place == place  # Добавляем фильтр по месту
    ).first()
    if existing:
        return False
    else:
        return True

def check_login_available(time_check: datetime.datetime, login:str, session):
    last_checkup = get_checkup_last_by_login(login, session)
    result = last_checkup['result']
    if result =="not_checkups":
        return True
    logger.info(f"result: {result}")
    last_time = result.checkup_time
    six_months_later = last_time + timedelta(days=180)  # ~6 месяцев
    return time_check >= six_months_later

def create_checkup(data: CheckupResponse, session) -> Optional[Checkup]:
    new_checkup = (Checkup(login=data.login, checkup_time=data.checkup_time, place=data.place, status="record"))
    logger.info(f"new_checkup{new_checkup}")
    write_checkup(new_checkup, session)
    write_checkup(new_checkup, session)
    return new_checkup

def delete_all_checkup(session) -> None:
    session.query(Checkup).delete()
    session.commit()

def delete_checkup_by_id(id: int, session) -> bool:
    checkup = session.get(Checkup, id)
    if checkup:
        session.delete(checkup)
        session.commit()
        return True
    return False


def update_checkup_status(
        id: int,
        session,
        new_status: str  # Новый статус для установки
) -> bool:
    checkup = session.get(Checkup, id)
    if checkup:
        checkup.status = new_status  # Изменяем статус
        session.commit()  # Сохраняем изменения
        return True
    return False

def create_checkup_test(session) -> Optional[Checkup]:
    new_checkup = (Checkup(login="testov@mail.ru", checkup_time=datetime.datetime.now(), place=2, status="record"))
    logger.info(f"new_checkup{new_checkup}")
    write_checkup(new_checkup, session)
    write_checkup(new_checkup, session)
    return new_checkup