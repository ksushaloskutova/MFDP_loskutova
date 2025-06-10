import pika
import json
import io
import time
from PIL import Image
from config import logger

from object_servise.ml_task import MLTaskAdd
from interaction_servise import ml_task_interaction as MLTaskServise
from database.database import session
from rabbitmq_workers.config import RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME
from fastapi import Depends

def create_connection(queue_name):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    logger.info(f"Попытка соединения с RabbitMQ на {RABBITMQ_HOST}:{RABBITMQ_PORT} как {RABBITMQ_USER}")
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(RABBITMQ_HOST, int(RABBITMQ_PORT), '/', credentials))
            logger.info("Соединение успешно установлено")

            channel = connection.channel()
            channel.queue_declare(queue=queue_name)
            logger.info(f"Очередь '{queue_name}' декларирована")
            return connection, channel  # Если успешно, возвращаем соединение и канал
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Ошибка подключения: {e}")
            time.sleep(5)  # Ждем 5 секунд перед следующей попыткой


def send_task_to_queue(image_data: Image.Image, task_add):
    connection, channel = create_connection(QUEUE_NAME)
    if not connection or not channel:
        logger.error("Не удалось установить соединение или канал")
        return

    img_byte_arr = io.BytesIO()
    image_data.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    payload = {
        "task_id": task_add.task_id,
        "password": task_add.password,
        "image": img_bytes.hex()
    }

    try:
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=json.dumps(payload))
        logger.info(f"Задача отправлена в очередь '{QUEUE_NAME}': {payload}")
    except Exception as e:
        logger.error(f"Ошибка при отправке задачи: {e}")
    finally:
        connection.close()
        logger.info("Соединение закрыто")


def consume_tasks(model):
    connection, channel = create_connection(QUEUE_NAME)
    if not connection or not channel:
        logger.error("Не удалось установить соединение или канал для потребления задач")
        return

    def callback(ch, method, properties, body):
        logger.info("Получено сообщение...")
        while True:
            try:
                data = json.loads(body)
                logger.info(f"Данные: {data}")

                task_id = data.get('task_id')
                password = data.get('password')
                img_bytes = bytes.fromhex(data["image"])
                image = Image.open(io.BytesIO(img_bytes))
                task_add = MLTaskAdd(task_id=task_id, password=password)
                task = MLTaskServise.create_task(task_add, model, image, session)
                logger.info(f"Задача {task} создана")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Задача {task_id} обработана и подтверждена")
            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {e}")

    try:
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        logger.info('Ожидание сообщений...')
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Ошибка при настройке потребления: {e}")
    finally:
        connection.close()
        logger.info("Соединение закрыто")