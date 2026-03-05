## 📋 **README.md**

```markdown
# P2P File Share — аналог station307

🚀 **P2P File Share** — это сервис для обмена файлами, работающий полностью в браузере через WebRTC (P2P) и поддерживающий загрузку через curl.

🔗 **Демо**: [https://station307.suhail35.ru](https://station307.suhail35.ru)

---

## ✨ Возможности

- 📤 **Отправка через браузер** — Drag-and-drop, прогресс-бар
- 📥 **Получение через браузер** — P2P передача, автоматическое скачивание
- 🖥️ **CLI режим (curl)** — как в station307
- 🔒 **Безопасность** — SSL, одноразовые ссылки, автоудаление через 1 час
- 🌐 **Работа через NAT** — встроенный TURN сервер
- 📁 **Русские имена файлов** — полная поддержка Unicode

---

## 🚀 Быстрый старт

### Отправка через браузер
1. Откройте [https://station307.suhail35.ru](https://station307.suhail35.ru)
2. Нажмите "Создать комнату"
3. Отправьте ссылку получателю

### Получение через браузер
1. Перейдите по полученной ссылке
2. Нажмите "Подключиться"
3. Файл скачается автоматически

### Отправка через curl
```bash
curl -T "мой_файл.docx" https://station307.suhail35.ru/
# Ответ: https://station307.suhail35.ru/d/abc12345
# Команда для скачивания:
curl -o "мой_файл.docx" https://station307.suhail35.ru/d/abc12345
```

---

## 🛠️ Технологии

| Компонент | Технология |
|-----------|------------|
| Бэкенд | Python + Flask + SocketIO |
| P2P | WebRTC (RTCPeerConnection, DataChannel) |
| TURN/STUN | Coturn |
| Веб-сервер | Nginx |
| Контейнеризация | Docker + Docker Compose |
| SSL | Let's Encrypt |

---

## 📦 Установка и запуск

### Требования
- Docker и Docker Compose
- Сервер с белым IP и открытыми портами 80/443
- Домен, привязанный к IP сервера

### Быстрый деплой
```bash
# Клонирование
git clone https://github.com/yourusername/p2p-file-share.git
cd p2p-file-share

# Настройка
cp .env.example .env
nano .env  # заполните свои данные

# Запуск
chmod +x deploy.sh
./deploy.sh
```

### Переменные окружения (.env)
```bash
DOMAIN=station307.suhail35.ru
PUBLIC_IP=123.123.123.123
SECRET_KEY=...  # openssl rand -hex 32
TURN_SECRET=... # openssl rand -hex 32
TURN_USERNAME=turnuser
TURN_PASSWORD=... # openssl rand -hex 16
```

---

## 📁 Структура проекта

```
p2p-file-share/
├── .env                      # Переменные окружения
├── docker-compose.yml        # Docker Compose конфиг
├── deploy.sh                  # Скрипт деплоя
├── signaling/                 # Python WebRTC signaling
│   ├── server.py
│   └── Dockerfile
├── turn/                      # TURN сервер
│   └── turnserver.conf
└── web/                       # Веб-интерфейс
    ├── html/
    │   ├── index.html
    │   ├── receive.html
    │   └── js/
    │       └── webrtc-client.js
    ├── nginx.conf
    └── ssl/                    # SSL сертификаты
```

---

## 🔧 API для curl

### Загрузка файла
```bash
curl -T file.txt https://ваш-домен/
```

### Ответ
```
https://ваш-домен/d/abc12345
curl -o file.txt https://ваш-домен/d/abc12345
```

### Скачивание
```bash
curl -o file.txt https://ваш-домен/d/abc12345
```

---

## 🧪 Тестирование

```bash
# Проверка здоровья
curl https://ваш-домен/health

# Отправка тестового файла
echo "test" > test.txt
curl -T test.txt https://ваш-домен/

# Проверка логов
docker-compose logs -f
```

---

## 🔒 Безопасность

- ✅ Все соединения через HTTPS
- ✅ Одноразовые ссылки (файл удаляется после скачивания)
- ✅ Автоудаление файлов через 1 час
- ✅ TURN с аутентификацией
- ✅ Секреты в .env, не в коде

---

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку (`git checkout -b feature/amazing`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте ветку (`git push origin feature/amazing`)
5. Откройте Pull Request

---

## 📄 Лицензия

MIT

---

## 🙏 Благодарности

- [station307.com](http://station307.com) — за вдохновение
- WebRTC сообществу
- Всем контрибьюторам

---

## 📞 Контакты

Автор: [Suhail Mamadkulov]
- GitHub: [@suhail35](https://github.com/suhail35)
- Email: suhail35@mail.ru
