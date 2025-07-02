from datetime import date, datetime, timedelta
from types import SimpleNamespace

from api import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Пример данных для создания чекапа
test_checkup_payload = {
    "login": "test_user",
    "place": 1,
    "checkup_time": (
        datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    ).isoformat(),
}


def test_create_checkup_success(monkeypatch):
    """
    Проверяет создание новой записи, когда слот свободен и ограничение по 6 месяцам соблюдено.
    """
    from interaction_servise import checkup_interaction

    monkeypatch.setattr(
        checkup_interaction, "check_time_available", lambda t, p, s: True
    )
    monkeypatch.setattr(
        checkup_interaction, "check_login_available", lambda t, login, s: True
    )
    monkeypatch.setattr(
        checkup_interaction,
        "create_checkup",
        lambda d, s: {"status": "success", "login": d.login},
    )

    response = client.post("/checkup/new", json=test_checkup_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_create_checkup_time_busy(monkeypatch):
    """
    Проверяет поведение, когда слот уже занят (409).
    """
    from interaction_servise import checkup_interaction

    monkeypatch.setattr(
        checkup_interaction, "check_time_available", lambda t, p, s: False
    )

    response = client.post("/checkup/new", json=test_checkup_payload)
    assert response.status_code == 409
    assert "уже занято" in response.json()["detail"]


def test_create_checkup_too_soon(monkeypatch):
    """
    Проверяет ограничение: запись реже чем раз в 6 месяцев.
    """
    monkeypatch.setattr(
        "interaction_servise.checkup_interaction.check_time_available",
        lambda t, p, s: True,
    )
    monkeypatch.setattr(
        "interaction_servise.checkup_interaction.check_login_available",
        lambda t, login, s: False,
    )
    monkeypatch.setattr(
        "interaction_servise.checkup_interaction.get_checkup_last_by_login",
        lambda login, s: {
            "result": SimpleNamespace(checkup_time=datetime.now() - timedelta(days=30))
        },
    )

    payload = {
        "login": "testuser",
        "checkup_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "place": 1,
    }

    response = client.post("/checkup/new", json=payload)

    assert response.status_code == 403
    assert "раз в 6 месяцев" in response.json()["detail"]


def test_get_available_time(monkeypatch):
    """
    Проверяет, что список доступного времени возвращается.
    """
    from interaction_servise import checkup_interaction

    monkeypatch.setattr(
        checkup_interaction,
        "get_available_time_slots",
        lambda s, d, r, p: ["10:00", "10:30", "11:00"],
    )

    params = {
        "date": date.today().isoformat(),
        "start_hour": 9,
        "end_hour": 12,
        "place": 1,
    }
    response = client.get("/checkup/time", params=params)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_last_checkup_found(monkeypatch):
    """
    Проверяет получение последней записи, если она существует.
    """
    from interaction_servise import checkup_interaction

    dummy_checkup = {
        "login": "test_user",
        "place": 1,
        "checkup_time": datetime.now().isoformat(),
    }
    monkeypatch.setattr(
        checkup_interaction,
        "get_checkup_last_by_login",
        lambda login, s: {"result": dummy_checkup},
    )

    response = client.get("/checkup/last", params={"login": "test_user"})
    assert response.status_code == 200
    assert response.json()["login"] == "test_user"


def test_get_last_checkup_not_found(monkeypatch):
    """
    Проверяет обработку случая, когда нет записей для пользователя.
    """
    from interaction_servise import checkup_interaction

    monkeypatch.setattr(
        checkup_interaction,
        "get_checkup_last_by_login",
        lambda login, s: {"result": "not_checkups"},
    )

    response = client.get("/checkup/last", params={"login": "unknown_user"})
    assert response.status_code == 404
    assert response.json()["code"] == "no_checkups"
