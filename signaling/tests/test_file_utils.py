import pytest
import os
from server import normalize_filename


def test_normalize_filename_url_decoding():
    """Тест декодирования URL-кодированных имен файлов."""
    encoded_name = "%D1%84%D0%B0%D0%B9%D0%BB.txt"  # 'файл.txt' в URL-кодировке
    expected = "файл.txt"
    assert normalize_filename(encoded_name) == expected


def test_normalize_filename_unicode_normalization():
    """Тест нормализации Unicode (NFC)."""
    # Символ 'é' представлен как 'e' + '́' (комбинирующий знак)
    decomposed = "cafe\u0301.txt"  # 'café.txt' в разложенной форме
    expected = "café.txt"  # 'café.txt' в составной форме (NFC)
    assert normalize_filename(decomposed) == expected


def test_normalize_filename_path_traversal_protection():
    """Тест защиты от атак Path Traversal."""
    malicious_name = "../../etc/passwd"
    # Функция должна вернуть только имя файла
    assert normalize_filename(malicious_name) == "passwd"

    malicious_name2 = "/home/user/secret.txt"
    assert normalize_filename(malicious_name2) == "secret.txt"


def test_normalize_filename_preserves_valid_unicode():
    """Тест сохранения валидных Unicode-имен с пробелами и символами."""
    complex_name = "Мой документ (v2).pdf"
    assert normalize_filename(complex_name) == complex_name

    special_chars = "file@#$%&().txt"
    assert normalize_filename(special_chars) == special_chars


def test_normalize_filename_empty_string():
    """Тест обработки пустой строки."""
    assert normalize_filename("") == ""


def test_normalize_filename_no_extension():
    """Тест обработки имени файла без расширения."""
    name_without_ext = "script"
    assert normalize_filename(name_without_ext) == name_without_ext