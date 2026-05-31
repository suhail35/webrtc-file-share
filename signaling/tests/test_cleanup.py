import pytest
import time
from unittest.mock import patch, MagicMock

# Импортируем приложение из server.py
from server import app, socketio

# Фикстура для создания тестового клиента
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_cleanup_old_files_removes_expired(client):
    """Тест, что /cleanup удаляет файлы старше 1 часа."""
    file_id_expired = 'expired123'
    file_id_recent = 'recent456'

    # Подготавливаем мок-данные
    with patch('server.app') as mock_app, \
         patch('server.os.remove') as mock_remove:

        # Создаем файлы: один просроченный, один свежий
        mock_app.files = {
            file_id_expired: {
                'path': f'/tmp/uploads/{file_id_expired}.txt',
                'name': 'old.txt',
                'created': time.time() - 3601  # 1 час и 1 секунда назад
            },
            file_id_recent: {
                'path': f'/tmp/uploads/{file_id_recent}.txt',
                'name': 'new.txt',
                'created': time.time() - 3599  # 1 час минус 1 секунда назад
            }
        }

        # Вызываем эндпоинт cleanup
        response = client.post('/cleanup')

        assert response.status_code == 200
        assert response.get_data(as_text=True) == "OK"

        # Проверяем, что был вызван os.remove только для просроченного файла
        mock_remove.assert_called_once_with(f'/tmp/uploads/{file_id_expired}.txt')
        # Проверяем, что файл удален из словаря
        assert file_id_expired not in mock_app.files
        # Проверяем, что свежий файл остался
        assert file_id_recent in mock_app.files


def test_cleanup_old_files_no_files_to_remove(client):
    """Тест, что /cleanup не удаляет файлы, если все они свежие."""
    file_id = 'fresh789'

    with patch('server.app') as mock_app, \
         patch('server.os.remove') as mock_remove:

        mock_app.files = {
            file_id: {
                'path': f'/tmp/uploads/{file_id}.txt',
                'name': 'fresh.txt',
                'created': time.time() - 1800  # 30 минут назад
            }
        }

        response = client.post('/cleanup')
        assert response.status_code == 200

        # Проверяем, что os.remove не был вызван
        mock_remove.assert_not_called()
        # Проверяем, что файл остался
        assert file_id in mock_app.files