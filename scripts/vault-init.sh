#!/bin/bash
# Скрипт инициализации Vault с учетными данными БД

set -e

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

echo "Ожидание запуска Vault..."
sleep 10

# Проверка доступности Vault
echo "Проверка подключения к Vault..."
max_retries=30
retries=0
while [ $retries -lt $max_retries ]; do
    if curl -s "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
        echo "Vault доступен"
        break
    fi
    retries=$((retries + 1))
    echo "Попытка $retries/$max_retries..."
    sleep 2
done

if [ $retries -eq $max_retries ]; then
    echo "Ошибка: Vault не запустился"
    exit 1
fi

# Включение KV v2 для хранилища секретов (если еще не включено)
echo "Проверка включения KV v2 секретов..."
curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
    -X GET "$VAULT_ADDR/v1/sys/mounts" | grep -q "secret/" || {
    echo "Включение KV v2 на пути secret/"
    curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
        -X POST "$VAULT_ADDR/v1/sys/mounts/secret" \
        -d '{"type":"kv","options":{"version":"2"}}'
}

echo "Инициализация Vault завершена успешно"
