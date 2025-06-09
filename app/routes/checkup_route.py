from fastapi import APIRouter, Depends
from database.database import get_session
from interaction_servise import checkup_interaction
from interaction_servise import user_interaction
from object_servise.checkup import TimeRequest, CheckupResponse
from fastapi import HTTPException, status
from datetime import date, time, datetime, timedelta
from fastapi import Depends, Query, HTTPException
from fastapi.responses import JSONResponse

import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



checkup_route = APIRouter()


@checkup_route.post("/new")
async def create_checkup(data: CheckupResponse, session=Depends(get_session)):
    if not checkup_interaction.check_time_available(data.checkup_time, data.place, session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Данное время уже занято, выберите другое"
        )

    # Проверяем временной интервал
    if not checkup_interaction.check_login_available(data.checkup_time, data.login, session):
        last_checkup = checkup_interaction.get_checkup_last_by_login(data.login, session)
        last_checkup = last_checkup["result"]
        last_date = last_checkup.checkup_time.strftime("%d.%m.%Y") if last_checkup else ""
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Нельзя записываться чаще чем раз в 6 месяцев. Ваша последняя запись была {last_date}"
        )


    try:
        new_checkup = checkup_interaction.create_checkup(data, session)
        return new_checkup
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при создании записи"
        )


@checkup_route.get("/time")
async def available_time(
    date: date = Query(..., description="Дата в формате YYYY-MM-DD"),
    start_hour: int = Query(..., ge=0, le=23, description="Начальный час (0-23)"),
    end_hour: int = Query(..., ge=0, le=23, description="Конечный час (0-23)"),
    place: int = Query(..., ge=0, le=23, description="Кабинка (1-5)"),
    session=Depends(get_session)
):
    hour_range = (start_hour, end_hour)
    available_time = checkup_interaction.get_available_time_slots(session, date, hour_range, place)
    return available_time

from fastapi import HTTPException
from fastapi.responses import JSONResponse


@checkup_route.get("/last")
async def get_last_checkup(login: str, session= Depends(get_session)):
    try:
        # Получаем результат из функции
        result = checkup_interaction.get_checkup_last_by_login(login, session)

        # Добавляем логирование результата
        logger.info(f"Результат вызова get_checkup_last_by_login: {result}")

        # Обрабатываем случай, когда запись не найдена
        if result["result"]=='not_checkups':
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "code": "no_checkups",
                    "message": "Записи не найдены"
                }
            )

        return result["result"]

    except Exception as e:
        logger.error(f"Ошибка при обработке: {str(e)}", exc_info=True)
        return {"error": "Произошла ошибка при обработке запроса"}