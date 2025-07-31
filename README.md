# 🤖 Meeting Scheduler Bot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-20.7-blue.svg)](https://python-telegram-bot.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://postgresql.org)
[![Google Calendar API](https://img.shields.io/badge/Google%20Calendar%20API-v3-green.svg)](https://developers.google.com/calendar)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46e3b7.svg)](https://render.com)

Интеллектуальный Telegram бот для автоматизации планирования встреч с **уникальной enterprise-grade диагностической системой v2.0**.

## ✨ Ключевые возможности

- 📅 **Двухэтапное бронирование**: сначала день, затем время
- 🗓️ **Google Calendar интеграция**: автоматическое создание встреч с Google Meet
- ⏰ **Система напоминаний**: за 7, 3 и 1 день до встречи  
- 👥 **Управление ролями**: Owner, Manager, Admin
- 🌍 **Русская локализация**: дни недели и интерфейс на русском
- 🔄 **Fallback режим**: работа без Google Calendar при необходимости

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/patriot-33/meeting-scheduler-bot.git
cd meeting-scheduler-bot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
# Обязательные переменные
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_TELEGRAM_IDS=ваш_telegram_id
DATABASE_URL=postgresql://user:password@localhost/meeting_scheduler

# Google Calendar (для полной функциональности)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
GOOGLE_CALENDAR_ID_1=calendar_id@group.calendar.google.com
GOOGLE_CALENDAR_ID_2=calendar_id@group.calendar.google.com

# Опциональные
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
```

### 4. Запуск бота
```bash
cd src
python main.py
```

## 📋 Основные команды

### Для всех пользователей:
- `/start` - Начало работы
- `/help` - Справка
- `/register` - Регистрация

### Для владельцев (Owner):
- `/owner` - Управление расписанием
  - Настроить дни и время
  - Добавить/удалить слоты
  - Заблокировать время

### Для руководителей (Manager):
- `/schedule` - Запланировать встречу
- `/profile` - Просмотр профиля
- `/active` / `/vacation` / `/sick` / `/trip` - Управление статусом

### Для администраторов:
- `/admin` - Панель администратора
- `/users` - Список пользователей
- `/stats` - Статистика системы

## 🏗️ Архитектура

```
src/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Модели базы данных
├── handlers/            # Обработчики Telegram команд
│   ├── registration.py
│   ├── manager.py
│   ├── owner.py
│   └── admin.py
├── services/           # Бизнес-логика
│   ├── meeting_service.py
│   ├── google_calendar.py
│   ├── owner_service.py
│   └── reminder_service.py
└── utils/              # Утилиты
    ├── decorators.py
    └── scheduler.py
```

## 🔧 Настройка Google Calendar

### 1. Создание Service Account
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект или выберите существующий
3. Включите Google Calendar API
4. Создайте Service Account и скачайте JSON ключ
5. Предоставьте доступ к календарю для Service Account

### 2. Настройка переменных
```bash
# Вставьте весь JSON как одну строку
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"..."}'

# ID календарей (найдите в настройках Google Calendar)
GOOGLE_CALENDAR_ID_1='primary'
GOOGLE_CALENDAR_ID_2='your-calendar@group.calendar.google.com'
```

## 🚀 Развертывание на Render.com

### 1. Подключение репозитория
1. Зарегистрируйтесь на [Render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите GitHub репозиторий

### 2. Настройка переменных окружения
В Render Dashboard добавьте все переменные из `.env.example`

### 3. Создание базы данных
1. Создайте PostgreSQL базу данных в Render
2. Подключите к Web Service

### 4. Проверка деплоя
- Health Check: `https://your-app.onrender.com/health`
- Логи деплоя в Render Dashboard

## 📱 Использование

### Процесс бронирования встречи:

1. **Выбор даты**:
```
/schedule → 📅 Выберите день для встречи:

[Понедельник, 31.07.2025 (5 слотов)]
[Вторник, 01.08.2025 (3 слота)]
```

2. **Выбор времени**:
```
🕐 Выберите время на Понедельник, 31.07.2025:

[09:00] [11:00] [14:00]
[15:00] [16:00]

[← Назад к выбору дня]
```

3. **Подтверждение**:
```
✅ Встреча успешно запланирована!

📅 Понедельник, 31.07.2025
🕐 14:00
🔗 Ссылка на встречу (Google Meet)
```

## 🧪 Тестирование

Бот поддерживает режим тестирования с одним владельцем:

1. Зарегистрируйтесь как Owner (используя ADMIN_TELEGRAM_IDS)
2. Настройте расписание через `/owner`
3. Зарегистрируйте тестового Manager
4. Протестируйте создание встречи через `/schedule`

## 📊 Мониторинг

### Health Check
```bash
curl https://your-app.onrender.com/health
```

### Логи
- **INFO**: Нормальные операции
- **WARNING**: Fallback режимы
- **ERROR**: Ошибки и проблемы

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 Лицензия

Этот проект использует лицензию MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🆘 Поддержка

- 📖 **Документация**: [SPECIFICATION.md](SPECIFICATION.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/patriot-33/meeting-scheduler-bot/issues)
- 💬 **Обсуждения**: [GitHub Discussions](https://github.com/patriot-33/meeting-scheduler-bot/discussions)

---

**Статус**: ✅ Production Ready  
**Версия**: 2.0  
**Последнее обновление**: 30.07.2025