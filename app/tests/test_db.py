import pytest
from sqlmodel import create_engine, SQLModel, Session
from database.database import get_session
from object_servise.ml_task import MLTask, MLTaskAdd
from object_servise.checkup import Checkup
from object_servise.user import User, UserResponse
from datetime import datetime, timedelta

# 📌 Фикстура тестовой сессии с SQLite in-memory
@pytest.fixture(scope="function")
def test_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    def override_get_session():
        yield session

    monkeypatch.setattr("database.database.get_session", override_get_session)

    return session

# ✅ Основной тест
def test_db_insert_fetch(test_session):
    # 🔹 Проверка добавления MLTask
    new_task = MLTask(MLTaskAdd(), "test_result")
    test_session.add(new_task)
    test_session.commit()
    task = test_session.query(MLTask).filter_by(result="test_result").first()
    assert task is not None
    assert task.task_id is not None

    # 🔹 Проверка добавления Checkup
    new_checkup = Checkup(
        login="test_user",
        checkup_time=datetime.now() + timedelta(days=1),
        place=1,
        status="record"
    )
    test_session.add(new_checkup)
    test_session.commit()
    checkup = test_session.query(Checkup).filter_by(login="test_user").first()
    assert checkup is not None
    assert checkup.place == 1

    # 🔹 Проверка добавления User
    new_user = UserResponse(
        login="test_login",
        password="password",
    )
    new_user=User(user = new_user, role = "user")
    test_session.add(new_user)
    test_session.commit()
    user = test_session.query(User).filter_by(login="test_login").first()
    assert user is not None
    assert user.role == "user"







