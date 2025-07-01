import pytest
import base64
from fastapi.testclient import TestClient
from api import app
from rabbitmq_workers import worker

client = TestClient(app)

def test_predict_and_result_flow(monkeypatch, test_session):
    img = base64.b64encode(b'fake').decode()
    payload = {"task_id": "loop", "password": "pwd", "image": img}
    # Мокаем RabbitMQ publish и task processing
    monkeypatch.setattr(worker, 'consume_tasks', lambda model: None)
    resp = client.post("/predict", json=payload)
    assert resp.status_code in (200,202)
    resp2 = client.get("/result/loop")
    assert resp2.status_code == 200
    assert resp2.json()['task_id'] == "loop"
