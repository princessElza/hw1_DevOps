#!/bin/bash
# Скрипт настройки Vault для локальной разработки
# Использует переменные из .env файла для инициализации Vault

set -e

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "Ошибка: файл .env не найден"
    echo "Пожалуйста, создайте .env файл на основе .env.example"
    exit 1
fi

# Загружаем переменные из .env
export $(cat .env | grep -v '^#' | xargs)

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

echo "=========================================="
echo "Настройка Vault для разработки"
echo "=========================================="
echo ""

# Проверка доступности Vault
echo "Проверка подключения к Vault..."
if ! curl -s -f "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
    echo "Ошибка: Vault не доступен по адресу $VAULT_ADDR"
    echo ""
    echo "Запустите контейнеры сначала:"
    echo "  docker-compose up -d vault postgres"
    exit 1
fi
echo "✓ Vault доступен"
echo ""

# Инициализация секретов БД
if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo "Ошибка: переменные DB_USER, DB_PASSWORD, DB_NAME должны быть установлены в .env"
    exit 1
fi

echo "Инициализация секретов БД в Vault..."
curl -s -X POST "$VAULT_ADDR/v1/secret/data/database/credentials" \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"data\": {
            \"DB_HOST\": \"${DB_HOST:-postgres}\",
            \"DB_PORT\": \"${DB_PORT:-5432}\",
            \"DB_USER\": \"$DB_USER\",
            \"DB_PASSWORD\": \"$DB_PASSWORD\",
            \"DB_NAME\": \"$DB_NAME\"
        }
    }" > /dev/null && echo "✓ Секреты БД инициализированы" || echo "✗ Ошибка инициализации"

# Инициализация конфигурации приложения
echo "Инициализация конфигурации приложения..."
curl -s -X POST "$VAULT_ADDR/v1/secret/data/app/config" \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "data": {
            "LOG_LEVEL": "INFO",
            "API_VERSION": "1.0.0",
            "MODEL_PATH": "/app/models/model.pkl"
        }
    }' > /dev/null && echo "✓ Конфигурация приложения инициализирована" || echo "✗ Ошибка инициализации"

echo ""
echo "=========================================="
echo "✓ Vault готов к использованию"
echo "=========================================="
echo ""
echo "Сохраненные секреты:"
echo "  - database/credentials (учетные данные БД)"
echo "  - app/config (конфигурация приложения)"
echo ""
echo "Совет: Для просмотра секретов используйте:"
echo "  curl -H 'X-Vault-Token: $VAULT_TOKEN' $VAULT_ADDR/v1/secret/data/database/credentials"
echo ""
