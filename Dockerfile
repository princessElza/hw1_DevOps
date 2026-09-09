FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё, что нужно
COPY src/ ./src/
COPY models/ ./models/
COPY data/*.npy ./data/
COPY config.ini .
COPY src/logger.py ./src/

# Копируем скрипт инициализации и конфиг

RUN mkdir -p logs

# Инициализация Vault при сборке контейнера
# Примечание: это будет выполнено при docker build если Vault доступен

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
