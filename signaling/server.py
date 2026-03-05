from flask import Flask, request, jsonify, send_file, make_response
from flask_socketio import SocketIO, emit, join_room, close_room
from flask_cors import CORS
import uuid
import time
import os
import urllib.parse
import unicodedata

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def normalize_filename(filename):
    """Нормализует имя файла для корректной работы с Unicode"""
    # Декодируем URL-кодировку
    filename = urllib.parse.unquote(filename)
    # Нормализуем Unicode (разные формы ввода)
    filename = unicodedata.normalize('NFC', filename)
    # Убираем path traversal, но сохраняем Unicode
    filename = os.path.basename(filename)
    return filename


# === Существующая WebRTC логика ===
@app.route('/health')
def health():
    return {'status': 'ok'}


@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    for room_id, room_data in list(rooms.items()):
        if room_data['sender'] == request.sid:
            emit('sender_disconnected', room=room_id)
            close_room(room_id)
            del rooms[room_id]
            print(f'Room {room_id} closed - sender disconnected')
        elif room_data['receiver'] == request.sid:
            room_data['receiver'] = None
            emit('receiver_disconnected', room=room_id)
            print(f'Receiver left room {room_id}')


@socketio.on('create_room')
def handle_create_room():
    room_id = str(uuid.uuid4())[:8]
    rooms[room_id] = {
        'sender': request.sid,
        'receiver': None,
        'created': time.time(),
        'file': None
    }
    join_room(room_id)
    emit('room_created', {'roomId': room_id})
    print(f'Room created: {room_id} by {request.sid}')


@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['roomId']
    if room_id not in rooms:
        emit('error', {'message': 'Комната не существует'})
        return
    room = rooms[room_id]
    if room['receiver'] is not None:
        emit('error', {'message': 'В комнате уже есть получатель'}, room=request.sid)
        return
    if room['sender'] == request.sid:
        emit('error', {'message': 'Вы не можете подключиться к своей комнате как получатель'}, room=request.sid)
        return
    room['receiver'] = request.sid
    join_room(room_id)
    emit('joined', {'roomId': room_id, 'role': 'receiver'}, room=request.sid)
    emit('peer_connected', {'roomId': room_id}, room=room_id, skip_sid=request.sid)
    print(f'Receiver {request.sid} joined room {room_id}')


@socketio.on('offer')
def handle_offer(data):
    room_id = data['room']
    if room_id in rooms:
        emit('offer', data['offer'], room=room_id, skip_sid=request.sid)


@socketio.on('answer')
def handle_answer(data):
    room_id = data['room']
    if room_id in rooms:
        emit('answer', data['answer'], room=room_id, skip_sid=request.sid)


@socketio.on('ice_candidate')
def handle_ice(data):
    room_id = data['room']
    if room_id in rooms:
        emit('ice_candidate', data['candidate'], room=room_id, skip_sid=request.sid)


# === НОВЫЕ маршруты для curl ===
@app.route('/', methods=['PUT', 'POST'])
@app.route('/<path:filename>', methods=['PUT', 'POST'])
def handle_upload(filename=None):
    """Единый endpoint для загрузки через curl"""

    # Генерируем ID файла
    file_id = str(uuid.uuid4())[:8]

    # ПОЛУЧАЕМ ИМЯ ФАЙЛА
    if request.headers.get('X-Filename'):
        # Из заголовка
        raw_filename = request.headers.get('X-Filename')
        print(f"Raw header filename: {raw_filename}")
    elif filename:
        # Из URL
        raw_filename = filename
        print(f"Raw URL filename: {raw_filename}")
    else:
        raw_filename = 'file.bin'
        print(f"Default filename")

    # Нормализуем имя
    original_filename = normalize_filename(raw_filename)
    print(f"Normalized filename: {original_filename}")

    # Получаем расширение из оригинального имени
    name_without_ext, ext = os.path.splitext(original_filename)
    if not ext:
        ext = '.bin'  # расширение по умолчанию

    # Сохраняем с ID и оригинальным расширением
    safe_name = f"{file_id}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, safe_name)

    # Сохраняем файл
    with open(filepath, 'wb') as f:
        f.write(request.data)

    # Сохраняем метаданные
    if not hasattr(app, 'files'):
        app.files = {}

    app.files[file_id] = {
        'path': filepath,
        'name': original_filename,
        'size': len(request.data),
        'created': time.time()
    }

    # Формируем ссылку и команду
    download_url = f"{request.host_url}d/{file_id}"
    curl_command = f"curl -o {original_filename} {download_url}"

    # Возвращаем полную информацию
    return f"""Файл загружен: {original_filename}
    Ссылка: {download_url}
    Команда для скачивания:
    {curl_command}

    """


@app.route('/d/<file_id>')
def handle_download(file_id):
    """Скачивание файла по ID"""

    if not hasattr(app, 'files') or file_id not in app.files:
        return "File not found", 404

    file_info = app.files[file_id]

    user_agent = request.headers.get('User-Agent', '').lower()

    if 'curl' in user_agent:
        # Для curl - отдаем простое имя в ASCII
        # Но curl сохранит имя из URL, поэтому переименуем файл на диске
        import shutil

        # Создаем копию с ASCII именем
        ascii_name = f"file_{file_id}.bin"
        ascii_path = os.path.join(UPLOAD_FOLDER, ascii_name)
        shutil.copy2(file_info['path'], ascii_path)

        # Отправляем ASCII файл
        response = send_file(
            ascii_path,
            as_attachment=True,
            download_name=ascii_name,
            mimetype='application/octet-stream'
        )

        # Удаляем оба файла после скачивания
        @response.call_on_close
        def cleanup():
            try:
                os.remove(file_info['path'])
                os.remove(ascii_path)
                del app.files[file_id]
            except:
                pass
    else:
        response = send_file(
            file_info['path'],
            as_attachment=True,
            download_name=file_info['name'],
            mimetype='application/octet-stream'
        )

    # Удаляем после скачивания
    @response.call_on_close
    def cleanup():
        try:
            os.remove(file_info['path'])
            del app.files[file_id]
        except:
            pass

    return response


# Очистка старых файлов
@app.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    now = time.time()
    if hasattr(app, 'files'):
        for file_id, info in list(app.files.items()):
            if now - info['created'] > 3600:  # 1 час
                try:
                    os.remove(info['path'])
                    del app.files[file_id]
                except:
                    pass
    return "OK"


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
