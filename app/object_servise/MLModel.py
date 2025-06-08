import numpy as np
import torch
import subprocess
import os
import tensorflow
from tensorflow.keras.models import load_model
from pydantic import BaseModel


class MLModel(BaseModel):
    model_name: str = "model_name"
    is_loaded: bool = False

    def load_model(self, model_path: str = "./MLModel") -> None:
        try:
            print("Загружаем модель через DVC")
            subprocess.run(["dvc", "pull", model_path], check=True)

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Модель {model_path} не найдена.")

            print("Загружаем модель в память.")
            self.model = load_model(model_path)
            self.is_loaded = True
            print("Модель успешно загружена!")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке модели: {str(e)}")


    def predict(self, image_array: np.ndarray) -> tuple[float, int]:
        if not self.is_loaded:
            raise Exception("Модель не загружена")
        y_prob = self.model.predict(image_array)
        y_pred = (y_prob > 0.5).astype(int)
        return y_prob, y_pred