# 📋 Meeting Scheduler Bot - Техническая Спецификация

## 🎯 Назначение
Telegram бот для автоматизации планирования созвонов между руководителями и владельцами бизнеса с автоматическими напоминаниями и контролем двухнедельных циклов встреч.

## 📱 Основная функциональность

### Ключевые возможности
- **Двухнедельные циклы встреч** - каждый руководитель должен провести созвон с владельцами бизнеса раз в 2 недели
- **Синхронизация доступности** - свободные слоты отображаются только когда оба владельца бизнеса доступны
- **Автоматические напоминания** - система уведомлений для предотвращения пропуска встреч
- **Контроль просроченных встреч** - автоматическое отслеживание и уведомления

## 🏗️ Архитектура

### Технологический стек
- **Python 3.11** - основной язык
- **python-telegram-bot[webhooks] 20.7** - Telegram Bot API с поддержкой webhooks
- **PostgreSQL** - база данных (Render.com)
- **SQLAlchemy 2.0.23** - ORM с поддержкой современного синтаксиса
- **Google Calendar API** - синхронизация календарей владельцев
- **APScheduler 3.10.4** - планировщик для напоминаний
- **Pydantic 2.5.2** - валидация конфигурации

### Структура проекта
```
meeting-scheduler-bot/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Точка входа с webhook поддержкой
│   ├── config.py              # Конфигурация (Pydantic)
│   ├── database.py            # Модели БД (SQLAlchemy 2.0)
│   ├── handlers/              # Обработчики команд
│   │   ├── __init__.py
│   │   ├── common.py          # Общие команды (/start, /help)
│   │   ├── admin.py           # Функции владельцев бизнеса
│   │   ├── manager.py         # Функции руководителей
│   │   └── registration.py    # Регистрация пользователей
│   ├── services/              # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── google_calendar.py # Google Calendar API
│   │   ├── meeting_service.py # Управление встречами
│   │   ├── reminder_service.py# Система напоминаний
│   │   └── user_service.py    # Управление пользователями
│   └── utils/                 # Утилиты
│       ├── __init__.py
│       ├── decorators.py      # Декораторы авторизации
│       ├── scheduler.py       # Настройка планировщика
│       └── health_check.py    # Health check с SQLAlchemy 2.0
├── requirements.txt           # Зависимости с webhook поддержкой
├── Dockerfile               # Docker конфигурация для Render
├── render.yaml             # Render.com деплой конфигурация
└── deploy_to_github.sh     # Скрипт для деплоя
```

## 📊 База данных

### Модель данных (PostgreSQL)
```sql
-- Роли пользователей
enum UserRole { ADMIN, MANAGER, PENDING }
-- ADMIN = владелец бизнеса
-- MANAGER = руководитель

-- Статусы пользователей  
enum UserStatus { ACTIVE, VACATION, SICK_LEAVE, BUSINESS_TRIP, DELETED }

-- Статусы встреч
enum MeetingStatus { SCHEDULED, COMPLETED, CANCELLED, NO_SHOW }

-- Пользователи
Table users {
  id: Integer (PK)
  telegram_id: Integer (Unique)
  telegram_username: String(255)
  first_name: String(255)
  last_name: String(255) 
  department: String(255)
  role: UserRole
  status: UserStatus
  created_at: DateTime
  updated_at: DateTime
}

-- Встречи
Table meetings {
  id: Integer (PK)
  manager_id: Integer (FK -> users.id)
  scheduled_time: DateTime
  google_event_id: String(255)
  google_meet_link: String(500)
  status: MeetingStatus
  created_at: DateTime
  updated_at: DateTime
}

-- Напоминания
Table reminders {
  id: Integer (PK)
  user_id: Integer (FK -> users.id)
  meeting_id: Integer (FK -> meetings.id, nullable)
  reminder_type: String(50)
  scheduled_for: DateTime
  sent: Boolean (default: false)
  sent_at: DateTime
  created_at: DateTime
}

-- Статистика
Table statistics {
  id: Integer (PK)
  user_id: Integer (FK -> users.id)
  total_meetings: Integer
  completed_meetings: Integer
  cancelled_meetings: Integer
  no_show_meetings: Integer
  last_meeting_date: DateTime
  updated_at: DateTime
}
```

## 🤖 Функциональность бота

### Команды для руководителей
- `/start` - Запуск бота и регистрация
- `/help` - Справка по командам
- `/schedule` - Назначить созвон (видны только свободные слоты обоих владельцев)
- `/my_meetings` - Мои запланированные встречи
- `/profile` - Информация о профиле
- `/vacation` - Установить статус "Отпуск"
- `/sick` - Установить статус "Больничный"  
- `/trip` - Установить статус "Командировка"
- `/active` - Вернуться к работе

### Команды для владельцев бизнеса (админов)
- `/admin` - Панель администратора
- `/pending` - Одобрение новых руководителей
- `/users` - Список всех пользователей
- `/stats` - Статистика по встречам
- `/broadcast` - Рассылка сообщений
- `/notifications` - Управление уведомлениями

## ⏰ Система напоминаний

### Для руководителей (если НЕ назначен созвон)
- **За 7 дней** до истечения 2 недель: "Не забудьте назначить двухнедельный созвон"
- **За 3 дня**: Повторное напоминание
- **За 1 день**: Последнее напоминание

### Для владельцев бизнеса
- **Если осталось 3 дня** и созвон не назначен: уведомление о руководителе без встречи
- **Ежедневная проверка в 9:00**: список просроченных встреч

### Для всех (при назначенной встрече)
- **За 1 день**: Напоминание о завтрашней встрече
- **За 1 час**: "Встреча начнется через час"

## ⚙️ Конфигурация

### Переменные окружения (.env)
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_IDS=123456789,987654321  # ID владельцев бизнеса

# Database (автоматически от Render)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google Calendar (календари владельцев)
GOOGLE_CALENDAR_ID_1=owner1@gmail.com
GOOGLE_CALENDAR_ID_2=owner2@gmail.com
GOOGLE_SERVICE_ACCOUNT_FILE=service_account_key.json

# Application
TIMEZONE=Europe/Moscow
DEBUG=false
LOG_LEVEL=INFO

# Webhook (для Render.com)
WEBHOOK_URL=https://meeting-scheduler-bot-fkp8.onrender.com
WEBHOOK_PATH=/webhook
PORT=10000  # Автоматически от Render
```

### Настройки доступности владельцев
```python
# Доступные временные слоты
available_slots = ["11:00", "13:00", "14:00", "16:00"]

# Рабочие дни
working_days = "Понедельник - Пятница"
```

## 🔄 Google Calendar интеграция

### Функциональность
- **Проверка доступности** - слот показывается только если оба владельца свободны
- **Создание событий** - автоматическое создание с Google Meet
- **Синхронизация** - отмена в боте = отмена в календарях
- **Кеширование** - 5 минут для оптимизации

## 🚀 Deployment на Render.com

### Успешно развернуто!
- **URL**: https://meeting-scheduler-bot-fkp8.onrender.com
- **Статус**: ✅ Live
- **База данных**: ✅ PostgreSQL подключена
- **Webhook**: ✅ Настроен и работает
- **Health Check**: ✅ Все проверки пройдены

### Исправленные проблемы
1. **SQLAlchemy 2.0 совместимость** - добавлен `text()` для SQL запросов
2. **Webhook зависимости** - обновлен requirements.txt с `python-telegram-bot[webhooks]`
3. **Event loop ошибки** - обработка исключений при shutdown
4. **Кодировка русского текста** - исправлены все сообщения

## 📈 Производительность

### Оптимизация для команды
```python
# Database connection pool
pool_size=5          # Оптимально для небольшой команды
max_overflow=2       # Дополнительные соединения
pool_recycle=3600    # Обновление каждый час
pool_pre_ping=True   # Проверка соединений

# Планировщик
reminder_check: каждые 15 минут
overdue_check: ежедневно в 9:00
```

## 🔒 Безопасность

### Реализованные меры
- **Декораторы авторизации** - `@require_admin`, `@require_registration`
- **Валидация конфигурации** - проверка при запуске
- **Защищенное логирование** - без токенов и паролей
- **Health check** - проверка всех компонентов перед запуском

## 📋 Версии

### v2.0.0 (30.07.2025) - Production Release
- ✅ Развернуто на Render.com
- ✅ Исправлены все критические ошибки
- ✅ SQLAlchemy 2.0 совместимость
- ✅ Webhook режим для production
- ✅ Полная русификация интерфейса

### v1.1.0 - Рефакторинг
- ✅ Оптимизация для малых команд
- ✅ Система health check
- ✅ Улучшенное логирование

### v1.0.0 - MVP
- Базовая функциональность
- Интеграция с Google Calendar
- Система напоминаний

---

## 📞 Поддержка
При возникновении вопросов обращайтесь к администраторам бота.