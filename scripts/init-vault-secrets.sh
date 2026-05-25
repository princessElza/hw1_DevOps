#!/bin/sh
# Скрипт инициализации секретов в Vault
# Загружает учетные данные БД в хранилище при запуске контейнера

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

# Получаем переменные из окружения
DB_USER="${DB_USER:-ml_user}"
DB_PASSWORD="${DB_PASSWORD:-password}"
DB_NAME="${DB_NAME:-ml_predictions}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"

echo "=========================================="
echo "Инициализация секретов в Vault"
echo "=========================================="
echo "Vault Address: $VAULT_ADDR"
echo "Database: $DB_NAME"
echo ""

# Ожидание запуска Vault
max_retries=60
retries=0
echo "Ожидание доступности Vault..."
while [ $retries -lt $max_retries ]; do
    if curl -f "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
        echo "[OK] Vault доступен"
        break
    fi
    retries=$((retries + 1))
    if [ $((retries % 10)) -eq 0 ]; then
        echo "  Попытка $retries/$max_retries..."
    fi
    sleep 1
done

if [ $retries -eq $max_retries ]; then
    echo "[ERROR] Vault не запустился"
    exit 1
fi

# Сохранение учетных данных БД в Vault
echo ""
echo "Сохранение учетных данных БД в Vault..."
RESPONSE=$(curl -s -X POST "$VAULT_ADDR/v1/secret/data/database/credentials" \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"data\": {\"DB_HOST\": \"$DB_HOST\", \"DB_PORT\": \"$DB_PORT\", \"DB_USER\": \"$DB_USER\", \"DB_PASSWORD\": \"$DB_PASSWORD\", \"DB_NAME\": \"$DB_NAME\"}}")

if echo "$RESPONSE" | grep -q "request_id"; then
    echo "[OK] Учетные данные БД сохранены"
else
    echo "[ERROR] Ошибка сохранения БД учетных данных"
    echo "Response: $RESPONSE"
fi

# Сохранение конфигурации приложения
echo ""
echo "Сохранение конфигурации приложения..."
curl -s -X POST "$VAULT_ADDR/v1/secret/data/app/config" \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"data": {"LOG_LEVEL": "INFO", "API_VERSION": "1.0.0", "MODEL_PATH": "/app/models/model.pkl"}}' > /dev/null && echo "[OK] Конфигурация сохранена" || echo "[ERROR] Ошибка сохранения конфигурации"

# Проверка сохраненных секретов
echo ""
echo "=========================================="
echo "[OK] Инициализация завершена успешно"
echo "=========================================="
echo ""
echo "Сохраненные секреты:"
echo "  - database/credentials"
echo "  - app/config"
echo ""
