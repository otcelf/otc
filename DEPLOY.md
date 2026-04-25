# Развёртывание OTC бота на сервере

## Способ 1: Простое развёртывание на VPS (Linux)

### Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Python 3.10+
sudo apt install -y python3.10 python3.10-venv python3-pip git

# Создать папку для проекта
mkdir -p /home/username/bots
cd /home/username/bots

# Клонировать репозиторий (или загрузить файлы)
git clone <repo-url> otc-bot
cd otc-bot
```

### Установка зависимостей

```bash
# Создать виртуальное окружение
python3.10 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### Настройка .env

```bash
# Скопировать и отредактировать .env
cp .env.example .env
nano .env

# Заполнить:
# BOT_TOKEN=ваш_токен
# BOT_USERNAME=ваш_username
# SUPPORT_USERNAME=поддержка
# OWNER_ID=ваш_id
# PROXY_URL=  # Оставить пустым на сервере!
```

### Способ А: Запуск в tmux/screen

```bash
# Установить tmux
sudo apt install -y tmux

# Запустить бота в tmux сессии
tmux new-session -d -s otc-bot 'cd /home/username/bots/otc-bot && source venv/bin/activate && python -m bot.main'

# Проверить логи
tmux attach-session -t otc-bot

# Остановить бота (внутри tmux)
Ctrl+C
```

### Способ Б: systemd сервис (рекомендуется)

1. Создать файл сервиса:

```bash
sudo nano /etc/systemd/system/otc-bot.service
```

2. Вставить содержимое:

```ini
[Unit]
Description=OTC Telegram Bot
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/bots/otc-bot
Environment="PATH=/home/username/bots/otc-bot/venv/bin"
ExecStart=/home/username/bots/otc-bot/venv/bin/python -m bot.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Активировать сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable otc-bot
sudo systemctl start otc-bot

# Проверить статус
sudo systemctl status otc-bot

# Смотреть логи
sudo journalctl -u otc-bot -f
```

---

## Способ 2: Docker развёртывание

1. Создать `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bot.main"]
```

2. Создать `docker-compose.yml`:

```yaml
version: '3.8'

services:
  otc-bot:
    build: .
    container_name: otc-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./bot.db:/app/bot.db
      - ./banner.jpg:/app/banner.jpg
```

3. Запустить:

```bash
docker-compose up -d

# Проверить логи
docker-compose logs -f otc-bot
```

---

## Способ 3: Heroku (если нужен облачный хостинг)

1. Установить Heroku CLI
2. Создать `Procfile`:

```
worker: python -m bot.main
```

3. Создать `runtime.txt`:

```
python-3.12.1
```

4. Развернуть:

```bash
heroku login
heroku create otc-bot-name
heroku config:set BOT_TOKEN=your_token
git push heroku main
```

---

## Рекомендуемый выбор

- **Для небольшого проекта**: systemd сервис (Способ Б) - просто и надёжно
- **Для production**: Docker + systemd или Docker Compose
- **Для облака**: Heroku, AWS, Railway, Render

## Мониторинг

Чтобы бот перезагружался при падении, используйте systemd (параметр `Restart=on-failure`) или Docker (параметр `restart: unless-stopped`).

## Смотреть логи

- **systemd**: `sudo journalctl -u otc-bot -f`
- **Docker**: `docker-compose logs -f otc-bot`
- **tmux**: `tmux attach-session -t otc-bot`
