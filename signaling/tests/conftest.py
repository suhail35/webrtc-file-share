import pytest
import threading
import time
from server import app, socketio


@pytest.fixture(scope='module')
def socketio_server():
    """Запускает SocketIO сервер в отдельном потоке для тестов."""
    # Запускаем сервер в отдельном потоке
    thread = threading.Thread(
        target=socketio.run,
        args=(app,),
        kwargs={
            'host': '127.0.0.1',
            'port': 5001,
            'debug': False,
            'use_reloader': False
        },
        daemon=True
    )
    thread.start()

    # Ждем запуска сервера
    time.sleep(1)

    yield

    # Останавливаем сервер (сложно в threading, но тесты короткие)
    # socketio.stop()


@pytest.fixture
def client():
    """Создает HTTP клиент для тестов."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
