from object_servise.ml_task import MLTask, MLTaskAdd
from typing import List, Optional
from PIL import Image

from object_servise.ml_model import MLModel
from config import logger

def get_all_tasks(session) -> List[MLTask]:
    return session.query(MLTask).all()

def get_task_by_id(id: int, session) -> Optional[List[MLTask]]:
    task = session.get(MLTask, id)
    if task:
        return task
    return None
def get_task_by_task_id(task_id: str, session) -> Optional[MLTask]:
    task= session.query(MLTask).filter(MLTask.task_id == task_id).first()
    return task if task else None

def password_verify(task: MLTask, password: str):
    return task.verify_password(password)


def form_task(question: MLTaskAdd, model: MLModel, input_data: Image.Image) -> MLTask:
    if question.validate(input_data):
        prepared_image_array = question.prepare_image(input_data)
        logger.info(f"prepared_image_array: {prepared_image_array}")
        question.save_images(input_data)
        logger.info("Image saved")

        result = str(question.predict(prepared_image_array, model))
        logger.info(f"Prediction result: {result}")

        task = MLTask(question, result)
        logger.info(f"Created task: {task}")
        return task
    else:
        logger.warning("Validation failed")
        return None  # Возврат None при неудаче валидации


def create_task(question: MLTaskAdd, model: MLModel, input_data: Image.Image, session) -> dict:
    try:
        task = form_task(question, model, input_data)
        if task is None:
            return {"error": "Task creation failed due to validation error."}

        session.add(task)
        session.commit()
        session.refresh(task)

        return {"message": f"Result: {task.result}"}
    except Exception as e:
        logger.error(f"Error while creating task: {e}")
        session.rollback()  # Откат изменений в случае ошибки
        return {"error": "Internal server error while creating task."}


def create_test_tsk(session):
    task_test = MLTaskAdd()
    task_to_db = MLTask(task_test, "result_test")
    session.add(task_to_db)
    session.commit()
    session.refresh(task_to_db)
