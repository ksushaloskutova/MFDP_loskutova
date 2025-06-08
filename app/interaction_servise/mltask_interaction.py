from object_servise.MLTask import MLTask, MLTaskAdd
from typing import List, Optional
from PIL import Image

from object_servise.MLModel import MLModel


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

def form_task(question : MLTaskAdd, model: MLModel, input_data: Image.Image) -> MLTask:
    if question.validate(input_data):
        prepared_image_array = question.prepare_image(input_data)
        question.save_images(input_data)
        result = question.predict(prepared_image_array, model)
        task = MLTask(question, result)
        return task

def create_task(question: MLTaskAdd, model: MLModel, input_data: Image.Image, session) -> dict:
    task = form_task(question, model, input_data)
    session.add(task)
    session.commit()
    session.refresh(task)
    return {"message": f"Result:{task.result}"}
