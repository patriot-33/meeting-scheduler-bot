# 🤖 Meeting Scheduler Bot

Автоматизированный Telegram бот для планирования встреч с менеджерами и отслеживания доступности сотрудников.

## ✨ Возможности

- 📅 **Автоматическое планирование встреч** с интеграцией Google Calendar
- 👥 **Управление пользователями** с системой ролей и модерацией
- 🔔 **Система напоминаний** за 7, 3 и 1 день до встречи
- 📊 **Статистика и аналитика** использования
- 🏢 **Управление статусами** (Активен, Отпуск, Больничный, Командировка)
- 👨‍💼 **Панель администратора** для управления пользователями

## 🚀 Быстрый старт

### 1. Требования
- Python 3.10+
- PostgreSQL база данных
- Telegram Bot Token (от @BotFather)
- Google Service Account для Calendar API

### 2. Установка
```bash
git clone https://github.com/patriot-33/meeting-scheduler-bot.git
cd meeting-scheduler-bot
pip install -r requirements.txt
```

### 3. Конфигурация
Создайте `.env` файл на основе `.env.example`:
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими токенами
```

### 4. Первый запуск
```bash
# Проверка готовности
python run_health_check.py

# Запуск бота
python -m src.main
```

## ⚙️ Конфигурация

### Обязательные переменные окружения
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_IDS=123456789,987654321
DATABASE_URL=postgresql://user:password@host:5432/dbname
GOOGLE_CALENDAR_ID_1=calendar1@gmail.com
GOOGLE_CALENDAR_ID_2=calendar2@gmail.com
```

### Google Calendar Setup
1. Создайте Service Account в Google Cloud Console
2. Скачайте `service_account_key.json`
3. Поделитесь календарями с email Service Account
4. Укажите путь к файлу в `GOOGLE_SERVICE_ACCOUNT_FILE`

## 🎯 Использование

### Команды для пользователей
- `/start` - Начать работу с ботом
- `/schedule` - Посмотреть доступные слоты и забронировать встречу
- `/my_meetings` - Мои запланированные встречи
- `/vacation` - Установить статус "Отпуск"
- `/active` - Вернуться к активному статусу

### Команды для администраторов
- `/admin` - Панель администратора
- `/pending` - Пользователи ожидающие одобрения
- `/users` - Все зарегистрированные пользователи
- `/stats` - Статистика использования бота
- `/broadcast` - Рассылка сообщений

## 🏗️ Архитектура

```
src/
├── main.py              # Точка входа
├── config.py           # Конфигурация
├── database.py         # Модели базы данных
├── handlers/           # Обработчики команд Telegram
├── services/           # Бизнес-логика
└── utils/             # Утилиты и декораторы
```

## 🚀 Deployment на Render.com

### Быстрый деплой
1. Подключите репозиторий к Render.com
2. Добавьте environment variables из `.env.example`
3. Загрузите содержимое `service_account_key.json` в переменную `GOOGLE_SERVICE_ACCOUNT_FILE`
4. Деплойте

### Проверка после деплоя
- Отправьте `/start` боту
- Проверьте логи в Render Dashboard
- Запустите health check: `python run_health_check.py`

## ⚡ Производительность

Оптимизировано для команд до 50 человек:
- **Connection pooling**: 5 соединений для базы данных
- **Кеширование**: Google Calendar API (5 минут TTL)
- **Планировщик**: проверка каждые 15 минут
- **Memory usage**: ~50-100MB

## 🔒 Безопасность

- ✅ Валидация конфигурации при запуске
- ✅ Авторизация через декораторы
- ✅ Защищенное логирование без sensitive данных
- ✅ Health check система

## 📋 Changelog

### v1.1.0 - Экспресс-оптимизация (текущая)
- ✅ Исправлены критические баги импортов
- ✅ Оптимизация для команд до 50 человек
- ✅ Улучшенная система логирования
- ✅ Health check система
- ✅ Защищенная конфигурация

### v1.0.0 - Базовая версия
- Регистрация и авторизация пользователей
- Планирование встреч
- Google Calendar интеграция
- Система напоминаний

---

**Разработано для эффективного управления встречами в небольших командах** 🎯