import pytest
from fastapi.testclient import TestClient
from api import app
from object_servise.ml_model import MLModel

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
def model():
    m = MLModel()
    m.load_model()  # можно загружать имитацию
    return m
