from object_servise.MLModel import MLModel
from sqlmodel import SQLModel, Field
from typing import Optional
import datetime
import base64
from PIL import Image
import numpy as np
import subprocess
import os
import tempfile
import hashlib

def delete_images_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Удалено изображение: {file_path}")

def delete_image(input_data_path: str) -> None:
    if os.path.exists(input_data_path):
        os.remove(input_data_path)
        print(f"Удалено изображение: {input_data_path}")
    else:
        print(f"Изображение не найдено: {input_data_path}")

import random
import string
from datetime import datetime

def generate_unique_id():
    """Генерация уникального ID на основе timestamp и случайных чисел"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(1000, 9999)
    return f"{timestamp}_{random_num}"

def generate_password(length=6):
    """Генерация случайного пароля из цифр и букв"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class MLTaskAdd(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(default_factory=generate_unique_id)  # ⚠️ Функция без скобок!
    password: str = Field(default_factory=lambda: generate_password(6))  # ⚠️ lambda для аргуме

    def validate_data(self, input_data: Image.Image) -> bool:
        if not isinstance(input_data, Image.Image):
            raise ValueError("Входное значение должно быть изображением формата PIL")
        return True

    def prepare_image(self, input_data: Image.Image) -> np.ndarray:
        image = input_data.resize((224, 224))  # Размеры могут варьироваться
        image_array = np.array(image).astype(np.float32) / 19.0
        image_array = np.transpose(image_array, (2, 0, 1))  # Изменение размерности
        image_array = np.expand_dims(image_array, axis=0)
        return image_array

    def predict(self, input_data: Image.Image, model: MLModel) -> np.ndarray:
        #return model.predict(input_data)
        return "предсказание"

    def save_images(self, input_data: Image.Image, directory_path: str ="images") -> None:
        try:
            result = subprocess.run(["dvc", "pull", directory_path], check=False)
            if result.returncode != 0:
                raise Exception("Ошибка при выполнении dvc pull.")
            print("dvc pull папки с изображениями")

            input_data.save(self.task_id)

            result = subprocess.run(["dvc", "add", directory_path], check=False)
            if result.returncode != 0:
                raise Exception("Ошибка при выполнении dvc add.")

            # Добавляем .dvc файл в Git
            #subprocess.run(["git", "add", f"{input_data_path}.dvc"], check=True)

            # Коммитим изменения
            #subprocess.run(["git", "commit", "-m", f"Добавлено новое изображение {input_data_path}"], check=True)

            # Пушкаем данные в удаленный репозиторий DVC
            print("Пушим новые данные через DVC")
            subprocess.run(["dvc", "push", directory_path], check=True)

            # Удаляем оригинальное изображение, так как оно теперь в DVC
            delete_images_in_directory(directory_path)
        except Exception as e:
            raise Exception(f"Ошибка при загрузке картинки: {str(e)}")



class MLTask(SQLModel, table=True):
    task_id: str
    id: Optional[int] = Field(default=None, primary_key=True)
    hash_password: str = Field(default=None)
    result: str
    time: datetime.datetime = Field(default_factory=datetime.datetime.now)

    def __init__(self, task: MLTaskAdd(), result) -> None:
        self.input_data_path = task.input_data_path
        self.hash_password = self.__password_hashing(task.password)
        self.result = result
        self.task_id = task.task_id

    def __password_hashing(self, password: str) -> str:
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + pwd_hash.hex()

    def verify_password(self, provided_password: str) -> bool:
        salt = bytes.fromhex(self.hash_password[:32])
        stored_hash = self.hash_password[32:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
        return pwd_hash.hex() == stored_hash


    def load_images(self, input_data_path: str, directory_path: str ="images") -> Image.Image:
        try:
            result = subprocess.run(["dvc", "pull", directory_path], check=False)
            if result.returncode != 0:
                raise Exception("Ошибка при выполнении dvc pull.")
            print("dvc pull папки с изображениями")

            if not os.path.exists(input_data_path):
                raise FileNotFoundError(f"Картинка {input_data_path} не найдена.")


            with Image.open(input_data_path) as image:
                return image.copy()  # Создание изменяемой копии изображения
        except Exception as e:
            raise Exception(f"Ошибка при загрузке картинки: {str(e)}")

    def delete_image_after_load(self, input_data_path: str, directory_path: str ="images") -> None:
        delete_images_in_directory(directory_path)





