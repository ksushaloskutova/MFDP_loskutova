from object_servise.ml_model import MLModel
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
import random
import string
from datetime import datetime

from config import logger


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
        """Подготавливает изображение для модели (размерность: 1,224,224,3)"""
        try:
            # Конвертируем в numpy array
            image_array = np.array(input_data)

            # Логируем исходную размерность
            logger.info(f"Исходная размерность: {image_array.shape}")

            # Обработка разных форматов:
            if len(image_array.shape) == 2:  # Grayscale (H,W)
                image_array = np.stack((image_array,) * 3, axis=-1)  # Конвертируем в RGB
            elif len(image_array.shape) == 3 and image_array.shape[-1] == 4:  # RGBA
                image_array = image_array[..., :3]  # Убираем альфа-канал
            elif len(image_array.shape) != 3 or image_array.shape[-1] != 3:
                raise ValueError("Неподдерживаемый формат изображения")

            # Ресайз и нормализация
            image = Image.fromarray(image_array).resize((224, 224))
            image_array = np.array(image).astype(np.float32) / 255.0

            # Добавляем batch-размерность (1,H,W,C)
            image_array = np.expand_dims(image_array, axis=0)

            # Проверка финальной размерности
            if image_array.shape != (1, 224, 224, 3):
                raise ValueError(f"Некорректная размерность после обработки: {image_array.shape}")

            logger.info(f"Готовый массив для модели: {image_array.shape}")
            return image_array

        except Exception as e:
            logger.error(f"Ошибка подготовки изображения: {str(e)}")
            raise

    def predict(self, prepared_array: np.ndarray, model: MLModel) -> np.ndarray:
        """Выполняет предсказание на подготовленных данных"""
        try:
            # Проверка размерности
            if prepared_array.shape != (1, 224, 224, 3):
                raise ValueError(f"Ожидается (1,224,224,3), получено: {prepared_array.shape}")

            # Пример реального предсказания:
            return model.predict(prepared_array)

        except Exception as e:
            logger.error(f"Ошибка предсказания: {str(e)}")
            raise

    def save_images(self, input_data: Image.Image, directory_path: str = "images") -> None:
        try:
            # Создаем директорию, если её нет
            os.makedirs(directory_path, exist_ok=True)

            logger.info(f"Сохраняем изображение в формате: jpg")

            # Формируем полный путь с расширением
            image_path = f"{directory_path}/{self.task_id}.jpg"

            # Выполняем DVC pull
            result = subprocess.run(["dvc", "pull", directory_path], check=False, capture_output=True, text=True)
            if result.returncode != 0:
               logger.info(f"DVC pull warning: {result.stderr}")

            # Приведение изображения к RGB, если это необходимо
            if input_data.mode != 'RGB':
                input_data = input_data.convert('RGB')

            # Сохраняем изображение с явным указанием формата
            input_data.save(image_path, format="JPEG")  # Используем верхний регистр для формата JPG

            # Добавляем в DVC
            result = subprocess.run(["dvc", "add", directory_path], check=False, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"DVC add failed: {result.stderr}")

            # Пушим изменения
            result = subprocess.run(["dvc", "push"], check=False, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"DVC push failed: {result.stderr}")

            # Очищаем временные файлы
            delete_images_in_directory(directory_path)

        except Exception as e:
            raise Exception(f"Ошибка при сохранении изображения: {str(e)}")


class MLTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str
    hash_password: str = Field(default=None)
    result: str
    time: datetime = Field(default_factory=datetime.now)

    def __init__(self, task: MLTaskAdd(), result) -> None:
        self.task_id = task.task_id
        self.hash_password = self.__password_hashing(task.password)
        self.result = result


    def __password_hashing(self, password: str) -> str:
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + pwd_hash.hex()

    def verify_password(self, provided_password: str) -> bool:
        salt = bytes.fromhex(self.hash_password[:32])
        stored_hash = self.hash_password[32:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
        return pwd_hash.hex() == stored_hash


    def load_images(self, directory_path: str ="images") -> Image.Image:
        try:
            data_path = f"{self.task_id}.jpg"
            result = subprocess.run(["dvc", "pull", directory_path], check=False)
            if result.returncode != 0:
                raise Exception("Ошибка при выполнении dvc pull.")
            print("dvc pull папки с изображениями")

            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Картинка {data_path} не найдена.")


            with Image.open(data_path) as image:
                return image.copy()  # Создание изменяемой копии изображения
        except Exception as e:
            raise Exception(f"Ошибка при загрузке картинки: {str(e)}")

    def delete_image_after_load(self, directory_path: str ="images") -> None:
        delete_images_in_directory(directory_path)






