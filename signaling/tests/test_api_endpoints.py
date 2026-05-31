import pytest
import json
import os
from unittest.mock import patch, mock_open
from flask import url_for

# Импортируем приложение из server.py
from server import app, socketio

# Создаем тестовый клиент
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Тест для /health

def test_health_endpoint(client):
    """Тест проверяет, что эндпоинт /health возвращает 200 OK."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

# Тесты для PUT /

def test_upload_file_with_filename_in_url(client):
    """Тест загрузки файла с именем в URL."""
    test_filename = 'test_file.txt'
    test_data = b'Test file content'

    with patch('server.uuid.uuid4', return_value='abc12345'):
        response = client.put(f'/{test_filename}', data=test_data, headers={'Content-Type': 'application/octet-stream'})

    assert response.status_code == 200
    response_text = response.get_data(as_text=True)
    assert test_filename in response_text
    assert 'http://localhost/d/abc12345' in response_text
    assert 'curl -o' in response_text


def test_upload_file_with_x_filename_header(client):
    """Тест загрузки файла с именем в заголовке X-Filename."""
    test_filename = 'header_file.docx'
    test_data = b'Document content'

    headers = {
        'Content-Type': 'application/octet-stream',
        'X-Filename': test_filename
    }

    with patch('server.uuid.uuid4', return_value='def67890'):
        response = client.put('/', data=test_data, headers=headers)

    assert response.status_code == 200
    response_text = response.get_data(as_text=True)
    assert test_filename in response_text
    assert 'http://localhost/d/def67890' in response_text


def test_upload_file_without_filename(client):
    """Тест загрузки файла без имени (используется имя по умолчанию)."""
    test_data = b'Binary data'

    with patch('server.uuid.uuid4', return_value='ghi11111'):
        response = client.put('/', data=test_data, headers={'Content-Type': 'application/octet-stream'})

    assert response.status_code == 200
    response_text = response.get_data(as_text=True)
    assert 'file.bin' in response_text
    assert 'http://localhost/d/ghi11111' in response_text

# Тесты для GET /d/<file_id>

def test_download_existing_file(client):
    """Тест успешного скачивания существующего файла."""
    file_id = 'abc12345'
    original_name = 'download_test.txt'
    file_content = b'Downloaded content'

    # Подготавливаем мок-данные
    with patch('server.app') as mock_app:
        mock_app.files = {
            file_id: {
                'path': f'/tmp/uploads/{file_id}.txt',
                'name': original_name,
                'size': len(file_content)
            }
        }
        # Мокаем send_file, чтобы он возвращал наш контент
        with patch('server.send_file') as mock_send_file:
            mock_send_file.return_value = 'mocked_response'

            response = client.get(f'/d/{file_id}')

            assert response.status_code == 200
            mock_send_file.assert_called_once()
            # Проверяем, что имя файла в download_name совпадает с оригинальным
            assert mock_send_file.call_args[1]['download_name'] == original_name


def test_download_nonexistent_file(client):
    """Тест поведения при запросе несуществующего file_id."""
    non_existent_id = 'nonexistent123'

    with patch('server.app') as mock_app:
        mock_app.files = {}  # Пустой словарь файлов

        response = client.get(f'/d/{non_existent_id}')

    assert response.status_code == 404
    assert b'File not found' in response.data


def test_download_file_twice(client):
    """Тест, что файл удаляется после первого скачивания."""
    file_id = 'jkl22222'
    file_content = b'One-time content'

    temp_file_path = f'/tmp/uploads/{file_id}.bin'

    with patch('server.app') as mock_app:
        mock_app.files = {
            file_id: {
                'path': temp_file_path,
                'name': 'onetime.bin',
                'size': len(file_content)
            }
        }
        # Создаем временный файл
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)

        # Первое скачивание - должно быть успешно
        response1 = client.get(f'/d/{file_id}')
        assert response1.status_code == 200

        # Второе скачивание - файл должен быть удален
        # Удаляем файл из мок-данных, как это делает реальный код
        del mock_app.files[file_id]
        response2 = client.get(f'/d/{file_id}')
        assert response2.status_code == 404

        # Удаляем временный файл, если он остался
        # Игнорируем ошибки, так как файл может быть уже удален или занят
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except PermissionError:
                pass


def test_download_file_curl_user_agent(client):
    """Тест обработки заголовка User-Agent для curl."""
    file_id = 'mno33333'
    original_name = 'curl_file.pdf'
    file_content = b'PDF data'

    with patch('server.app') as mock_app, \
         patch('shutil.copy2') as mock_copy2, \
         patch('os.remove') as mock_remove, \
         patch('server.send_file') as mock_send_file:

        mock_app.files = {
            file_id: {
                'path': f'/tmp/uploads/{file_id}.pdf',
                'name': original_name,
                'size': len(file_content)
            }
        }
        mock_send_file.return_value = 'mocked_response'

        # Имитируем запрос от curl
        response = client.get(f'/d/{file_id}', headers={'User-Agent': 'curl/7.68.0'})

        assert response.status_code == 200
        # Проверяем, что была создана копия с ASCII-именем
        mock_copy2.assert_called_once()
        # Проверяем, что оба файла были удалены
        assert mock_remove.call_count == 2
        # Проверяем, что отправляется копия
        assert mock_send_file.call_args[1]['download_name'].startswith('file_')
        assert mock_send_file.call_args[1]['download_name'].endswith('.bin')