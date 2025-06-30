from object_servise.ml_model import MLModel
import threading
from rabbitmq_workers import worker as WorkerServise
import time

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Отключает GPU

# Для TensorFlow
import tensorflow as tf
tf.config.set_visible_devices([], 'GPU')


if __name__ == "__main__":
    model = MLModel()
    model.load_model()

    worker_thread = threading.Thread(
        target=WorkerServise.consume_tasks,
        args=(model,),
        daemon=True
    )
    worker_thread.start()

    # Бесконечное ожидание с обработкой прерывания
    try:
        while True:
            time.sleep(1)
            if not worker_thread.is_alive():
                print("Worker thread died, exiting...")
                break
    except KeyboardInterrupt:
        print("Received interrupt, shutting down")