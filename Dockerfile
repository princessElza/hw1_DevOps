FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости (обновленная версия)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY src/ ./src/
COPY models/ ./models/
COPY data/*.npy ./data/
COPY config.ini .

# Создаём папку для логов
RUN mkdir -p logs

# Открываем порт для API
EXPOSE 8000

# Команда для запуска API сервиса
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]