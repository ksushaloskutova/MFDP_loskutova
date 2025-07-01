import pytest
from fastapi.testclient import TestClient
from api import app
import base64
from PIL import Image
from io import BytesIO

client = TestClient(app)

# 1. Проверка, что API запущен, возвращает 404 или ответ по корневому маршруту
def test_healthcheck_or_root():
    resp = client.get("/")
    assert resp.status_code in (200, 404)

# 2. Запрос на predict без изображения должен вернуть ошибку валидации
def test_predict_missing_image_field():
    payload = {"task_id": "1", "password": "pwd"}
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422

# 3. Некорректная строка image (не hex/base64) — должен быть 400 или 422
def test_predict_invalid_image_format():
    payload = {"task_id": "1", "password": "pwd", "image": "bad_data"}
    resp = client.post("/predict", json=payload)
    assert resp.status_code in (400, 422)

# 4. Корректный формат base64 изображения — ожидается успешный ответ
def test_predict_valid_image_base64():
    img = Image.open('tests/Image.png')
    buf = BytesIO()
    img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()
    payload = {"task_id": "test", "password": "pwd", "image": img_str}
    resp = client.post("/predict", json=payload)
    assert resp.status_code in (200, 202)

# 5. Повторная отправка уникального task_id — тест idempotency/дубли
def test_predict_duplicate_task_id():
    img = Image.new("RGB", (224, 224), color="grey")
    buf = BytesIO(); img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()
    payload = {"task_id": "dup_id", "password": "pwd", "image": img_str}

    resp1 = client.post("/predict", json=payload)
    resp2 = client.post("/predict", json=payload)
    assert resp1.status_code in (200, 202)
    assert resp2.status_code in (200, 202, 409)

# 6. Некорректные credentials — ожидаем 401 Unauthorized
def test_predict_bad_credentials():
    img = Image.new("RGB", (224, 224), color="blue")
    buf = BytesIO(); img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()
    payload = {"task_id": "3", "password": "wrong", "image": img_str}
    resp = client.post("/predict", json=payload)
    assert resp.status_code in (401, 403)

# 7. Проверяем структуру успешного ответа — status и task_id
def test_predict_response_structure():
    """
    Проверяем, что при успешном submit возвращается json с task_id и status.
    """
    img = Image.new("RGB", (224, 224), color="green")
    buf = BytesIO(); img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()
    payload = {"task_id": "5", "password": "pwd", "image": img_str}
    resp = client.post("/predict", json=payload)
    assert resp.status_code in (200, 202)
    data = resp.json()
    assert "task_id" in data and data["task_id"] == "5"
    assert "status" in data

# 8. Проверяем эндпоинт получения результата /result/{task_id}
def test_get_result_nonexistent():
    resp = client.get("/result/nonexistent")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        d = resp.json()
        assert "status" in d

# 9. Полный submit + fetch: интеграционный тест
def test_submit_and_fetch_result(monkeypatch):
    # Мок модели и RabbitMQ, если доступно — или проверка структуры ответа /result
    img = Image.new("RGB", (224, 224), color="yellow")
    buf = BytesIO(); img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()
    payload = {"task_id": "int_test", "password": "pwd", "image": img_str}
    resp_post = client.post("/predict", json=payload)
    assert resp_post.status_code in (200, 202)

    resp_get = client.get(f"/result/int_test")
    assert resp_get.status_code in (200, 404)
    if resp_get.status_code == 200:
        res = resp_get.json()
        assert "task_id" in res and res["task_id"] == "int_test"
        assert "status" in res
