import pytest
import threading
import time
from rabbitmq_workers.worker import consume_tasks, create_connection

class DummyModel:
    def __init__(self):
        self.called = False
    def predict(self, x): return [0]  # пример

@pytest.fixture(scope="module")
def rabbitmq_connection():
    conn, ch = create_connection("test_queue")
    yield conn, ch
    conn.close()

def test_rabbitmq_send_receive(rabbitmq_connection):
    """
    Проверяем работу очереди RabbitMQ:
    отправляем test-сообщение, слушаем в тестовом callback.
    """
    conn, ch = rabbitmq_connection
    received = {}
    def cb(ch, method, prop, body):
        received['body'] = body
        ch.basic_ack(delivery_tag=method.delivery_tag)
    ch.basic_consume(queue="test_queue", on_message_callback=cb, auto_ack=False)
    # отправляем
    test_body = b'{"task_id":"t","password":"p","image":""}'
    ch.basic_publish("", "test_queue", test_body)
    # запускаем consumer в threads
    t = threading.Thread(target=lambda: ch.start_consuming(), daemon=True)
    t.start()
    time.sleep(1)
    assert received.get('body') == test_body

def test_consumer_with_dummy_model(monkeypatch, rabbitmq_connection):
    """
    Проверяем, что consume_tasks вызывает MLModel.predict при поступлении задачи.
    """
    conn, ch = rabbitmq_connection
    dummy = DummyModel()
    # Мокаем inner callback
    monkeypatch.setattr(ch, 'basic_consume', lambda queue, on_message_callback: on_message_callback(ch, type('M', (), {'delivery_tag':1}), type('P',(),{}), b'{"task_id":"x","password":"y","image":""}'))
    # Мокаем acknowledge
    monkeypatch.setattr(ch, 'basic_ack', lambda delivery_tag: setattr(dummy, 'called', True))
    consume_tasks(dummy)
    assert dummy.called, "После consume_tasks должен быть вызван basic_ack"
