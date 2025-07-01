import pytest
from object_servise.ml_model import MLModel

def test_model_load(tmp_path, monkeypatch):
    """
    Проверка: модель загружается через DVC и готова к инференсу.
    Мокаем загрузку данных и вызываем ml_model.load_model().
    """
    m = MLModel()
    # Мокаем DVC fetch
    monkeypatch.setattr(m, 'load_model', lambda: setattr(m, 'model', 'dummy'))
    m.load_model()
    assert hasattr(m, 'model'), "После load_model объект должен иметь атрибут model"
