#!/bin/sh
# Проверяет, что Kafka Consumer получил сообщение от API.

set -eu

MAX_RETRIES=10
RETRY=0

while [ "$RETRY" -lt "$MAX_RETRIES" ]; do
    if docker compose --env-file .cd.env logs --no-color kafka-consumer | grep -q 'Kafka consumer получил результат'; then
        echo "Kafka Consumer получил сообщение"
        exit 0
    fi

    RETRY=$((RETRY + 1))
    echo "Ожидание Kafka Consumer: $RETRY/$MAX_RETRIES"
    sleep 2
done

echo "Kafka Consumer не получил сообщение"
exit 1
