import numpy as np
import subprocess
import os
import tensorflow
from tensorflow.keras.models import load_model
from pydantic import BaseModel
from config import logger
from tensorflow.keras.models import Model
from typing import Optional
from pydantic import BaseModel


class MLModel(BaseModel):
    model_name: str = "model_name"
    is_loaded: bool = False
    model: Optional[Model] = None

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


    def predict(self, image_array: np.ndarray) -> tuple[float, int]:
        if not self.is_loaded:
            raise Exception("Модель не загружена")
        y_prob = self.model.predict(image_array)
        y_pred = (y_prob > 0.5).astype(int)
        return y_prob, y_pred