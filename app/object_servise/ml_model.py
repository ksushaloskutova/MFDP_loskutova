import numpy as np
import subprocess
import os
from tensorflow.keras.models import load_model
from config import logger
from tensorflow.keras.models import Model
from typing import Optional

class MLModel:
    def __init__(self, model_name="model_name"):
        self.model_name = model_name
        self.is_loaded = False
        self.model = None

    class Config:
        arbitrary_types_allowed = True

    def load_model(self, model_path: str = "./model") -> None:
        try:
            logger.info("Загружаем модель через DVC")
            subprocess.run(["dvc", "pull", model_path], check=True)
            model_path = f"{model_path}/model.h5"
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Модель {model_path} не найдена.")

            logger.info("Загружаем модель в память.")
            self.model = load_model(model_path)
            self.is_loaded = True
            logger.info("Модель успешно загружена!")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке модели: {str(e)}")


    def predict(self, image_array: np.ndarray) -> str:
        if not self.is_loaded:
            raise Exception("Модель не загружена")
        y_prob = self.model.predict(image_array)
        y_pred = (y_prob > 0.5).astype(int)
        confidence = y_prob[0][0]  # первое значение из первого массива
        label = y_pred[0][0]  # первое значение из второго массива

        formatted_result = f"Confidence: {confidence:.4f}, Label: {label}"
        return formatted_result