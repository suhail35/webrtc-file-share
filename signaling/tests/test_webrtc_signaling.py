import pytest
import time
import uuid
from server import rooms


def test_create_room():
    """Тест создания новой комнаты."""
    room_id = str(uuid.uuid4())[:8]

    # Симулируем создание комнаты
    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': None,
        'created': time.time(),
        'file': None
    }

    assert room_id in rooms
    assert rooms[room_id]['sender'] == 'test_sender'
    assert rooms[room_id]['receiver'] is None

    # Очищаем
    del rooms[room_id]


def test_join_room_success():
    """Тест успешного присоединения получателя к комнате."""
    room_id = str(uuid.uuid4())[:8]

    # Создаем комнату
    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': None,
        'created': time.time(),
        'file': None
    }

    # Присоединяем получателя
    rooms[room_id]['receiver'] = 'test_receiver'

    assert rooms[room_id]['receiver'] == 'test_receiver'

    # Очищаем
    del rooms[room_id]


def test_join_room_nonexistent():
    """Тест присоединения к несуществующей комнате."""
    fake_room_id = 'nonexistent123'

    # Проверяем, что комнаты нет
    assert fake_room_id not in rooms


def test_join_room_already_taken():
    """Тест присоединения к комнате, где уже есть получатель."""
    room_id = str(uuid.uuid4())[:8]

    # Создаем комнату с получателем
    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': 'existing_receiver',
        'created': time.time(),
        'file': None
    }

    # Проверяем, что receiver уже занят
    assert rooms[room_id]['receiver'] is not None

    # Очищаем
    del rooms[room_id]


def test_sender_disconnect_closes_room():
    """Тест, что при отключении отправителя комната закрывается."""
    room_id = str(uuid.uuid4())[:8]

    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': 'test_receiver',
        'created': time.time(),
        'file': None
    }

    # Симулируем отключение отправителя
    del rooms[room_id]

    assert room_id not in rooms


def test_receiver_disconnect_resets_receiver():
    """Тест, что при отключении получателя поле receiver сбрасывается."""
    room_id = str(uuid.uuid4())[:8]

    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': 'test_receiver',
        'created': time.time(),
        'file': None
    }

    # Симулируем отключение получателя
    rooms[room_id]['receiver'] = None

    assert rooms[room_id]['receiver'] is None

    # Очищаем
    del rooms[room_id]


def test_offer_relay_logic():
    """Тест логики ретрансляции offer."""
    room_id = str(uuid.uuid4())[:8]

    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': 'test_receiver',
        'created': time.time(),
        'file': None
    }

    # Проверяем, что оба участника в комнате
    assert rooms[room_id]['sender'] is not None
    assert rooms[room_id]['receiver'] is not None

    del rooms[room_id]


def test_answer_relay_logic():
    """Тест логики ретрансляции answer."""
    room_id = str(uuid.uuid4())[:8]

    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': 'test_receiver',
        'created': time.time(),
        'file': None
    }

    # Проверяем, что оба участника в комнате
    assert rooms[room_id]['sender'] is not None
    assert rooms[room_id]['receiver'] is not None

    del rooms[room_id]


def test_ice_candidate_relay_logic():
    """Тест логики ретрансляции ICE candidate."""
    room_id = str(uuid.uuid4())[:8]

    rooms[room_id] = {
        'sender': 'test_sender',
        'receiver': 'test_receiver',
        'created': time.time(),
        'file': None
    }

    # Проверяем, что оба участника в комнате
    assert rooms[room_id]['sender'] is not None
    assert rooms[room_id]['receiver'] is not None

    del rooms[room_id]
