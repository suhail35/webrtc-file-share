FROM python:3.11-slim

# 1. Установка зависимостей системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 2. Создание пользователя (безопасность)
RUN useradd -m -u 1000 appuser

# 3. Рабочая директория
WORKDIR /app

# 4. Копируем только requirements (для кэширования)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn eventlet

# 5. Копируем остальной код
COPY --chown=appuser:appuser . .

# 6. Смена пользователя
USER appuser

# 7. Экспорт порта
EXPOSE 5000

# 8. Запуск через gunicorn (production-ready)
CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:5000", "server:app"]