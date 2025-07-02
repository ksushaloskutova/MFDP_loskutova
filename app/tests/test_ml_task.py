from io import BytesIO

from api import app
from fastapi.testclient import TestClient
from PIL import Image

client = TestClient(app)


# 1. Проверка, что API запущен, возвращает 404 или ответ по корневому маршруту
def test_healthcheck_or_root():
    resp = client.get("/")
    assert resp.status_code in (200, 404)


client = TestClient(app)


def create_test_image():
    # Создает простое черное изображение 224x224 JPEG
    image = Image.new("RGB", (224, 224), color="black")
    buf = BytesIO()
    image.save(buf, format='JPEG')
    buf.seek(0)
    return buf


def test_create_task_success():
    """
    Проверяет успешную отправку изображения на обработку.
    Ожидается task_id и пароль в ответе.
    """
    img = create_test_image()
    response = client.post("/ml_task/", files={"file": ("test.jpg", img, "image/jpeg")})

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "password" in data
    assert data["message"] == "Your photo has been sent for processing."


def test_create_task_invalid_format():
    """
    Проверяет ошибку при загрузке некорректного изображения (текст вместо изображения).
    """
    response = client.post(
        "/ml_task/", files={"file": ("fake.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 200  # Возможно, 422 лучше
    assert response.json()["status"] == "error"


def test_get_all_tasks():
    """
    Проверяет, что GET / возвращает список задач.
    """
    response = client.get("/ml_task/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_task_invalid_id():
    """
    Проверка запроса результата по несуществующему ID.
    """
    response = client.get("/ml_task/wrong-id", params={"password": "fakepass"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task with supplied task_id does not exist"


def test_get_task_wrong_password(monkeypatch):
    """
    Проверка обработки неверного пароля при запросе задачи.
    """

    # Мокаем сервис

    class FakeTask:
        result = "Pathology"
        password_hash = "fakehash"

        def load_images(self):
            return Image.new("RGB", (224, 224))

        def delete_image_after_load(self):
            pass

    from interaction_servise import ml_task_interaction as MLTaskService

    monkeypatch.setattr(MLTaskService, "get_task_by_task_id", lambda tid, s: FakeTask())
    monkeypatch.setattr(MLTaskService, "password_verify", lambda task, pwd: False)

    response = client.get("/ml_task/any-id", params={"password": "wrongpass"})
    assert response.status_code == 404
    assert "incorrect" in response.json()["detail"]
