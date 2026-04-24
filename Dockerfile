FROM python:3.12-slim

WORKDIR /app

# Установить системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копировать зависимости
COPY requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копировать весь код
COPY . .

# Запустить бота
CMD ["python", "-m", "bot.main"]
