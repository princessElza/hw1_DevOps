# Image classifier: лабораторная №4

Сервис классифицирует изображения на `spider` и `slug`.

## Схема работы

`FastAPI -> Kafka Producer -> Kafka -> Kafka Consumer`

После каждого предсказания API отправляет в Kafka результат: класс, уверенность и имя файла. Отдельный сервис `kafka-consumer` принимает сообщение и пишет его в лог.

Данные для подключения к PostgreSQL по-прежнему получает только сервис API из Vault:

`Vault -> FastAPI -> PostgreSQL`

## Запуск

Создай локальный `.env` на основе `.env.example`, затем запусти:

```bash
docker compose up --build
```

Swagger API доступен по адресу `http://localhost:8000/docs`.

## Проверка Kafka

1. Отправь запрос в `/predict` или загрузи изображение в `/predict_image`.
2. В логах `kafka-consumer` появится строка `Kafka consumer получил результат`.

CI собирает Docker image и отправляет его в DockerHub. CD поднимает все контейнеры через `docker-compose`, проверяет API, получение секретов БД из Vault и доставку сообщения в Kafka Consumer.
