from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from fastapi.responses import StreamingResponse, RedirectResponse
from io import BytesIO
from PIL import Image
from typing import List
from object_servise.ml_task import MLTask, MLTaskAdd
from object_servise.ml_model import MLModel
from database.database import get_session
from interaction_servise import user_interaction as  UserServise
from interaction_servise import ml_task_interaction as  MLTaskServise
from config import logger
from rabbitmq_workers import worker as Worker
from fastapi import Query

# from rabbitmq_workers import worker as Worker

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import JSONResponse
import base64
import io

ml_task_router = APIRouter(tags=["MLTask"])
#templates = Jinja2Templates(directory="templates")


@ml_task_router.get("/", response_model=List[MLTask])
async def retrieve_all_tasks(session = Depends(get_session)) -> List[MLTask]:
    return MLTaskServise.get_all_tasks(session = session)


from io import BytesIO

@ml_task_router.get("/{task_id}")  # Используем параметр пути
async def retrieve_task_result(
    task_id: str,  # Параметр пути (не Query)
    password: str = Query(..., description="Password for the task"),  # Параметр запроса
    session = Depends(get_session)
):
    # Получаем задачу из базы данных
    task = MLTaskServise.get_task_by_task_id(task_id, session)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task with supplied task_id does not exist"
        )
    if not (MLTaskServise.password_verify(task, password)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="the password is incorrect"
        )
    # Загружаем изображение
    image = task.load_images()
    task.delete_image_after_load()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="I can't upload the image"
        )

    # Подготавливаем изображение для отправки
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG')  # Или другой формат
    img_byte_arr.seek(0)
    message = MLTaskServise.format_prediction_result(task.result)
    # Возвращаем JSON с результатом и изображением в base64
    return {
        "result": message,
        "image": base64.b64encode(img_byte_arr.getvalue()).decode('utf-8'),
        "task_id": task_id,
        "status": "completed"
    }


#Функция создания MLTask: проверка баланса, передача работы в Worker(отслеживает),
#передача клиенту id task
@ml_task_router.post("/")
async def create_task(
        file: UploadFile = File(...),
        session=Depends(get_session)
):
    # Читаем и конвертируем в PIL Image
    contents = await file.read()
    try:
        image = Image.open(BytesIO(contents))

        # Создаём объекты
        task_add = MLTaskAdd()
        Worker.send_task_to_queue(image, task_add)
        return {"message": "Your photo has been sent for processing.", "task_id": task_add.task_id, "password":
            task_add.password}

    except Exception as e:
        logger.error(f"Ошибка API: {str(e)}")
        return {
            "status": "error",
            "message": f"Ошибка: {str(e)}",

        }


