import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image
from api import app
import io

client = TestClient(app)

def create_test_image():
    # Создает простое черное изображение 224x224 JPEG
    image = Image.new("RGB", (224, 224), color="black")
    buf = BytesIO()
    image.save(buf, format='JPEG')
    buf.seek(0)
    return buf

def test_predict_and_result_flow(monkeypatch):
    """
    Тестирует полный цикл: отправка изображения на /ml_task/ и получение результата с /ml_task/{task_id}
    """

    # Заглушка для send_task_to_queue, чтобы не слать в RabbitMQ
    from rabbitmq_workers import worker as Worker
    monkeypatch.setattr(Worker, "send_task_to_queue", lambda image, task_add: None)

    # Мокаем получение задачи из БД и изображение
    from interaction_servise import ml_task_interaction
    from types import SimpleNamespace

    dummy_image = create_test_image()

    monkeypatch.setattr(
        ml_task_interaction,
        "get_task_by_task_id",
        lambda task_id, session: SimpleNamespace(
            task_id=task_id,
            password="testpassword",
            result="positive",
            load_images=lambda: dummy_image,
            delete_image_after_load=lambda: None
        )
    )

    monkeypatch.setattr(
        ml_task_interaction,
        "password_verify",
        lambda task, password: True
    )

    files = {"file": ("test.jpg", dummy_image, "image/jpeg")}
    response = client.post("/ml_task/", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "password" in data

    # Проверяем получение результата
    result_resp = client.get(f"/ml_task/{data['task_id']}?password={data['password']}")
    assert result_resp.status_code == 200
    assert result_resp.json()["status"] == "completed"
    assert "result" in result_resp.json()
    assert "image" in result_resp.json()