import pytest
from api import app, init_db
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def test_session(monkeypatch):
    """
    Создаём тестовую in-memory БД.
    """
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Инициализируем БД через init_db
    monkeypatch.setattr('api.database.SessionLocal', TestingSessionLocal)
    init_db()
    return TestingSessionLocal()

def test_db_insert_fetch(test_session):
    """
    Тестируем вставку и выборку MLTask из БД.
    """
    # Пример вставки записи
    from object_servise.ml_task import MLTask
    new = MLTask(task_id='123', status='pending')
    test_session.add(new)
    test_session.commit()
    fetched = test_session.query(MLTask).filter_by(task_id='123').one()
    assert fetched.status == 'pending'
