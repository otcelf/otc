# Инструкция по деплою на BotHost.ru

## Шаг 1: Подготовка
1. Токен бота: `8790397267:AAG9-mgu2R0Ly1NpMQNsmFPp42cWboGtLS8`
2. GitHub репозиторий: https://github.com/otcelf/otc
3. Ветка: `master`

## Шаг 2: Создание проекта на BotHost.ru
1. Создать новый проект
2. Выбрать "Python"
3. Подключить GitHub репозиторий: `https://github.com/otcelf/otc`
4. Ветка: `master`

## Шаг 3: Настройка переменных окружения
Добавить следующие переменные:
```
BOT_TOKEN=8790397267:AAG9-mgu2R0Ly1NpMQNsmFPp42cWboGtLS8
BOT_USERNAME=StellarGarantBot
SUPPORT_USERNAME=StellarOTCSupport
OWNER_ID=6930148555
BANNER_PATH=banner.jpg
DB_PATH=bot.db
```

## Шаг 4: Загрузка файлов
Загрузить файл `banner.jpg` в корень проекта на хостинге

## Шаг 5: Команда запуска
В Procfile уже прописано: `worker: python app.py`

Или можно использовать: `python bot/main.py`

## Шаг 6: Запуск
1. Нажать "Deploy" или "Start"
2. Проверить логи - не должно быть ошибок
3. Написать боту `/start` - должен ответить с новым баннером и текстом "Stellar OTC"

## Проверка версии
Бот должен показывать:
- ✅ "Stellar OTC" (не "ELF OTC")
- ✅ Новый баннер
- ✅ Кнопки должны работать
- ✅ Команда `/freeteam` должна работать

## Если запустилась старая версия:
1. Удалить проект полностью
2. Создать заново
3. Или сделать `git reset --hard origin/master` на хостинге
