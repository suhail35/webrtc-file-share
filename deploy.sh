#!/bin/bash

set -e  # Прерывать при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем деплой P2P File Share...${NC}"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo "Создайте .env на основе .env.example"
    exit 1
fi

# Загрузка переменных
set -a
source .env
set +a

# Проверка обязательных переменных
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ DOMAIN не задан в .env${NC}"
    exit 1
fi

if [ -z "$PUBLIC_IP" ]; then
    echo -e "${RED}❌ PUBLIC_IP не задан в .env${NC}"
    echo "Добавьте PUBLIC_IP=ваш.внешний.ip в .env"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "5f8c9e3d2a1b4f7e8d2c3a5b6e7f8a9b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f" ]; then
    echo -e "${YELLOW}⚠️  SECRET_KEY не изменен! Используйте сгенерированный ключ.${NC}"
fi

# Проверка доступности портов
echo -e "${YELLOW}🔍 Проверка портов...${NC}"
for port in 80 443; do
    if ss -tuln | grep -q ":$port "; then
        echo -e "${RED}❌ Порт $port уже занят!${NC}"
        echo "Остановите другие сервисы, использующие порт $port"
        exit 1
    fi
done

# Остановка старых контейнеров (если есть)
echo -e "${YELLOW}🛑 Остановка старых контейнеров...${NC}"
docker-compose -f docker-compose.yml down 2>/dev/null || true

# Получение SSL сертификатов (если нет)
if [ ! -d "./web/ssl/live/${DOMAIN}" ]; then
    echo -e "${YELLOW}🔐 Получение SSL сертификатов для ${DOMAIN}...${NC}"

    # Создание директории для сертификатов
    mkdir -p ./web/ssl

    # Запуск certbot
    docker run -it --rm \
        -p 80:80 \
        -v "$(pwd)/web/ssl:/etc/letsencrypt" \
        certbot/certbot certonly --standalone \
        -d ${DOMAIN} -d www.${DOMAIN}

    # Проверка успешности получения сертификатов
    if [ ! -d "./web/ssl/live/${DOMAIN}" ]; then
        echo -e "${RED}❌ Ошибка получения SSL сертификатов!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ SSL сертификаты уже существуют${NC}"

    # Проверка срока действия сертификатов
    if [ -f "./web/ssl/live/${DOMAIN}/fullchain.pem" ]; then
        expiry=$(openssl x509 -enddate -noout -in "./web/ssl/live/${DOMAIN}/fullchain.pem" | cut -d= -f2)
        echo -e "${GREEN}📅 Сертификат действителен до: $expiry${NC}"
    fi
fi

# Создание необходимых директорий
echo -e "${YELLOW}📁 Создание директорий...${NC}"
mkdir -p ./signaling/logs ./turn/logs

# Запуск контейнеров
echo -e "${YELLOW}🐳 Запуск контейнеров...${NC}"
docker-compose -f docker-compose.yml up -d --build

# Ожидание запуска
echo -e "${YELLOW}⏳ Ожидание запуска сервисов...${NC}"
sleep 10

# Проверка статуса
echo -e "${YELLOW}✅ Проверка статуса...${NC}"
docker-compose -f docker-compose.yml ps

# Проверка здоровья сервисов
echo -e "${YELLOW}🏥 Проверка здоровья сервисов...${NC}"
for service in signaling-server web-server; do
    status=$(docker inspect --format='{{.State.Health.Status}}' webrtc-${service} 2>/dev/null || echo "not found")
    if [ "$status" == "healthy" ]; then
        echo -e "${GREEN}✅ $service: $status${NC}"
    else
        echo -e "${RED}❌ $service: $status${NC}"
    fi
done

# Проверка доступности сайта
echo -e "${YELLOW}🌐 Проверка доступности сайта...${NC}"
if curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/health | grep -q "200"; then
    echo -e "${GREEN}✅ Сайт доступен по адресу: https://${DOMAIN}${NC}"
else
    echo -e "${RED}❌ Сайт не отвечает!${NC}"
    echo "Проверьте логи: docker-compose logs"
fi

echo -e "${GREEN}🎉 Деплой завершен!${NC}"
echo -e "${GREEN}📱 Сайт доступен по адресу: https://${DOMAIN}${NC}"
echo -e "${YELLOW}📊 Для просмотра логов: docker-compose logs -f${NC}"