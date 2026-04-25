# Ребрендинг на Stellar OTC

## ✅ Что обновлено:

### Название:
- **ELF OTC** → **Stellar OTC**

### Username бота:
- **@GiftOtcRobot** → **@StellarGarantBot**

### Username поддержки:
- **@ElfOtcSupport** / **@EIfOtcSupport** → **@StellarOTCSupport**

---

## 📝 Обновленные файлы:

1. `README.md` - название проекта
2. `bot/handlers/start.py` - приветствие и инструкция для воркеров
3. `bot/handlers/deal_create.py` - все тексты сделок
4. `bot/keyboards/main.py` - ссылка на поддержку
5. `bot/services/i18n.py` - переводы (RU/EN)
6. `site/index.html` - главная страница сайта
7. `site/projection.html` - страница проекции

---

## ⚙️ Что нужно обновить вручную:

### 1. Файл `.env`:
```env
BOT_TOKEN=<новый_токен_от_@StellarGarantBot>
BOT_USERNAME=StellarGarantBot
SUPPORT_USERNAME=StellarOTCSupport
OWNER_ID=6930148555
BANNER_PATH=banner.jpg
DB_PATH=bot.db
```

### 2. На BotHost.ru:
- Обновить переменные окружения
- Перезапустить бота

### 3. Получить новый токен:
1. Зайти в @BotFather
2. Создать нового бота `/newbot`
3. Назвать: **Stellar OTC**
4. Username: **@StellarGarantBot**
5. Скопировать токен в `.env`

---

## 🎨 Дополнительно (опционально):

- Обновить `avatar.jpg` и `banner.jpg` с новым логотипом
- Обновить описание бота в @BotFather
- Настроить команды бота в @BotFather

---

Все готово! 🚀
