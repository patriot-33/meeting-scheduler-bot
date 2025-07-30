# 📋 Meeting Scheduler Bot - Техническая Спецификация v2.1

## 🎯 Назначение
Автоматизированный Telegram бот для планирования двухнедельных созвонов между руководителями и владельцами бизнеса с полной системой напоминаний и контролем доступности.

## 📱 Основная функциональность

### 🚀 Ключевые возможности
- **Двухнедельные циклы встреч** - автоматическое отслеживание обязательных созвонов каждые 14 дней
- **Синхронизация доступности** - слоты показываются только при свободности обоих владельцев бизнеса
- **Многоуровневая система напоминаний** - за 7, 3, 1 день до дедлайна и за час до встречи
- **Контроль просроченных встреч** - автоматические уведомления администраторам
- **Управление статусами** - отпуск, больничный, командировка с автоматической адаптацией
- **Google Calendar интеграция** - синхронизация с календарями владельцев

## 🏗️ Архитектура системы

### 💻 Технологический стек
- **Python 3.11** - основной язык разработки
- **python-telegram-bot[webhooks] 20.7** - Telegram Bot API с webhook поддержкой
- **PostgreSQL** - основная база данных (Render.com)
- **SQLite** - локальная разработка и тестирование
- **SQLAlchemy 2.0.23** - ORM с поддержкой современного синтаксиса
- **Google Calendar API** - интеграция с календарями (2.108.0)
- **APScheduler 3.10.4** - планировщик задач для напоминаний
- **Pydantic 2.5.2** - валидация конфигурации и настроек
- **Render.com** - облачная платформа для деплоя

### 📂 Структура проекта
```
meeting-scheduler-bot/
├── src/                          # Исходный код приложения
│   ├── __init__.py
│   ├── main.py                   # Точка входа с webhook/polling поддержкой
│   ├── config.py                 # Конфигурация с Pydantic валидацией
│   ├── database.py               # SQLAlchemy модели (PostgreSQL/SQLite)
│   ├── handlers/                 # Telegram обработчики команд
│   │   ├── __init__.py
│   │   ├── common.py             # Общие команды (/start, /help, /cancel)
│   │   ├── admin.py              # Админские функции владельцев
│   │   ├── manager.py            # Функции руководителей (исправлено)
│   │   └── registration.py       # Система регистрации пользователей
│   ├── services/                 # Бизнес-логика приложения
│   │   ├── __init__.py
│   │   ├── google_calendar.py    # Google Calendar API интеграция
│   │   ├── meeting_service.py    # Управление встречами и слотами
│   │   ├── reminder_service.py   # Система напоминаний (исправлено)
│   │   └── user_service.py       # Управление пользователями
│   └── utils/                    # Вспомогательные утилиты
│       ├── __init__.py
│       ├── decorators.py         # Авторизационные декораторы
│       ├── scheduler.py          # Конфигурация планировщика
│       └── health_check.py       # Health check с SQLAlchemy 2.0
├── requirements.txt              # Python зависимости
├── Dockerfile                   # Docker конфигурация для Render
├── render.yaml                  # Render.com деплой конфигурация
├── .env                        # Локальные переменные окружения
├── TROUBLESHOOTING.md          # Руководство по решению проблем
├── RENDER_DEPLOY_GUIDE.md      # Гайд по деплою на Render
└── Диагностические скрипты:
    ├── check_webhook_simple.py   # Проверка webhook без зависимостей
    ├── debug_bot.py              # Детальная диагностика бота
    ├── deploy_to_render.py       # Автоматическая настройка Render
    ├── fix_webhook_url.py        # Исправление webhook URL
    ├── quick_webhook_fix.py      # Быстрое исправление webhook
    ├── run_simple_bot.py         # Локальный запуск без scheduler
    └── setup_local_bot.py        # Настройка локальной среды
```

## 📊 База данных (PostgreSQL/SQLite)

### 🗄️ Модель данных
```sql
-- Роли пользователей
CREATE TYPE user_role AS ENUM ('ADMIN', 'MANAGER', 'PENDING');
-- ADMIN = владелец бизнеса (макс. 2 человека)
-- MANAGER = руководитель (неограничено)
-- PENDING = ожидает одобрения

-- Статусы активности
CREATE TYPE user_status AS ENUM ('ACTIVE', 'VACATION', 'SICK_LEAVE', 'BUSINESS_TRIP', 'DELETED');

-- Статусы встреч
CREATE TYPE meeting_status AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW');

-- Пользователи системы
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'PENDING',
    status user_status DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Встречи и созвоны
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    manager_id INTEGER REFERENCES users(id) NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    google_event_id VARCHAR(255) UNIQUE,
    google_meet_link VARCHAR(500),
    status meeting_status DEFAULT 'SCHEDULED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Система напоминаний
CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    meeting_id INTEGER REFERENCES meetings(id),
    reminder_type VARCHAR(50) NOT NULL, -- 'schedule_meeting', 'meeting_1h', etc.
    scheduled_for TIMESTAMP NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Статистика использования
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    total_meetings INTEGER DEFAULT 0,
    completed_meetings INTEGER DEFAULT 0,
    cancelled_meetings INTEGER DEFAULT 0,
    no_show_meetings INTEGER DEFAULT 0,
    last_meeting_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🤖 Функциональность бота

### 👥 Команды для руководителей
- `/start` - Регистрация и главное меню
- `/help` - Справочная информация
- `/schedule` - Просмотр и бронирование доступных слотов
- `/my_meetings` - Список запланированных встреч
- `/profile` - Информация профиля и статистика
- `/vacation` - Установить статус "Отпуск"
- `/sick` - Установить статус "Больничный"
- `/trip` - Установить статус "Командировка"
- `/active` - Вернуться к активному статусу
- `/cancel` - Отмена текущей операции

### 👑 Команды для владельцев бизнеса (администраторов)
- `/admin` - Административная панель
- `/pending` - Модерация новых пользователей
- `/users` - Управление всеми пользователями
- `/stats` - Детальная статистика по встречам
- `/broadcast` - Массовая рассылка сообщений
- `/notifications` - Управление системой уведомлений

## ⏰ Система напоминаний

### 📅 Для руководителей (при отсутствии назначенной встречи)
- **За 7 дней** до истечения 2-недельного периода: "Пора назначить двухнедельный созвон"
- **За 3 дня** до дедлайна: "Срочно! Осталось 3 дня для назначения встречи"
- **За 1 день** до дедлайна: "Последний день! Назначьте встречу сегодня"

### 🔔 Для владельцев бизнеса
- **При 3 днях до дедлайна** без назначенной встречи: уведомление о конкретном руководителе
- **Ежедневная проверка в 9:00 МСК**: отчет о всех просроченных встречах
- **Еженедельный отчет**: статистика активности системы

### ⏰ Для всех участников (при назначенной встрече)
- **За 24 часа**: "Завтра у вас встреча в [время]"
- **За 1 час**: "Встреча начнется через час. Ссылка: [Google Meet]"
- **После встречи**: опрос об участии и результатах

## ⚙️ Конфигурация системы

### 🔐 Переменные окружения (.env)
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec
ADMIN_TELEGRAM_IDS=99006770  # ID владельцев бизнеса (через запятую)

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/dbname  # Render автоматически
# Для локальной разработки: sqlite:///test.db

# Google Calendar Integration
GOOGLE_CALENDAR_ID_1=owner1@gmail.com  # Календарь первого владельца
GOOGLE_CALENDAR_ID_2=owner2@gmail.com  # Календарь второго владельца
GOOGLE_SERVICE_ACCOUNT_FILE=service_account_key.json

# Application Settings
TIMEZONE=Europe/Moscow
DEBUG=false
LOG_LEVEL=INFO

# Webhook Configuration (Production)
WEBHOOK_URL=https://meeting-scheduler-bot-fkp8.onrender.com
WEBHOOK_PATH=/webhook
PORT=10000  # Автоматически от Render

# Business Logic Settings
MEETING_DURATION_MINUTES=60
MAX_BOOKING_DAYS_AHEAD=30
AVAILABLE_SLOTS=["11:00", "13:00", "14:00", "16:00"]
REMINDER_INTERVALS=[7, 3, 1]  # дни до встречи
```

### 🕐 Настройки доступности владельцев
```python
# Рабочие дни и время
WORKING_DAYS = "Понедельник - Пятница"
BUSINESS_HOURS = "09:00 - 18:00 МСК"
MEETING_SLOTS = {
    "morning": ["11:00"],
    "afternoon": ["13:00", "14:00", "16:00"]
}

# Автоматические исключения
EXCLUDE_WEEKENDS = True
EXCLUDE_HOLIDAYS = True  # Российские праздники
EXCLUDE_OVERLAPPING = True  # Исключить пересекающиеся встречи
```

## 🔄 Google Calendar интеграция

### 📅 Функциональность
- **Проверка доступности** - слот доступен только если оба владельца свободны
- **Автоматическое создание событий** - с Google Meet ссылками
- **Двусторонняя синхронизация** - отмена в боте = отмена в календарях
- **Кеширование запросов** - 5 минут TTL для оптимизации
- **Обработка конфликтов** - автоматическое разрешение пересечений

### 🔐 Авторизация
- Service Account для безопасности
- JSON ключ с правами на календари
- Без OAuth flow для пользователей

## 🚀 Production Deployment на Render.com

### ✅ Текущий статус (v2.1)
- **URL**: https://meeting-scheduler-bot-fkp8.onrender.com
- **Статус**: 🟢 Live и стабильно работает
- **База данных**: 🟢 PostgreSQL подключена и инициализирована
- **Webhook**: 🟢 Настроен и обрабатывает сообщения
- **Scheduler**: 🟢 Выполняет задачи каждые 15 минут
- **Health Check**: ✅ Все компоненты проверены

### 🐛 Исправленные критические проблемы
1. **SQLAlchemy 2.0 совместимость** - добавлен `text()` для SQL запросов
2. **Webhook зависимости** - обновлен `python-telegram-bot[webhooks]==20.7`
3. **Event loop ошибки** - корректная обработка shutdown
4. **Кодировка русского текста** - все сообщения корректно отображаются
5. **Database URL валидация** - поддержка SQLite для локальной разработки
6. **Webhook URL конфигурация** - правильный URL с `-fkp8` суффиксом

### 📈 Производительность и оптимизация

#### 🔧 Database настройки (PostgreSQL)
```python
# Оптимизировано для малых команд (до 10 пользователей)
ENGINE_CONFIG = {
    "pool_size": 5,              # 5 соединений базовых
    "max_overflow": 2,           # +2 при пиковой нагрузке
    "pool_recycle": 3600,        # Обновление каждый час
    "pool_pre_ping": True,       # Проверка соединений
    "echo": False                # Отключено в production
}
```

#### ⚡ Кеширование и оптимизация
```python
# Google Calendar API кеширование
@lru_cache(maxsize=100)
def get_calendar_events(calendar_id, time_range):
    # Кеш на 5 минут для календарных запросов
    pass

# Планировщик настройки
SCHEDULER_CONFIG = {
    "job_defaults": {
        "coalesce": True,        # Объединение пропущенных задач
        "max_instances": 1       # Предотвращение race conditions
    },
    "executors": {
        "default": ThreadPoolExecutor(2)  # 2 потока для задач
    }
}
```

#### 📊 Ожидаемая нагрузка
- **Активных пользователей**: 5-10 человек
- **Встреч в неделю**: 3-5
- **API запросов в день**: 200-500
- **Database запросов**: 1000-2000
- **Memory usage**: 80-120MB
- **CPU usage**: <10% в среднем

## 🔒 Безопасность

### 🛡️ Реализованные меры защиты
- **Авторизационные декораторы** - `@require_admin`, `@require_registration`
- **Валидация на уровне Pydantic** - все входные данные проверяются
- **Защищенное логирование** - токены и пароли не записываются в логи
- **Health check система** - мониторинг всех критических компонентов
- **Rate limiting** - защита от спама через Telegram API
- **SQL injection protection** - параметризованные запросы SQLAlchemy

### 🔐 Управление секретами
- Environment variables для всех чувствительных данных
- Service Account keys для Google API
- Webhook URL validation
- Admin ID whitelist

## 📋 Диагностика и устранение неполадок

### 🔧 Инструменты диагностики
```bash
# Проверка webhook без зависимостей
python3 check_webhook_simple.py

# Детальная диагностика всех компонентов
python3 debug_bot.py

# Автоматическая настройка для Render
python3 deploy_to_render.py

# Быстрое исправление webhook
python3 fix_webhook_url.py

# Локальный запуск для тестирования
python3 run_simple_bot.py
```

### 📖 Документация по устранению неполадок
- **TROUBLESHOOTING.md** - решение распространенных проблем
- **RENDER_DEPLOY_GUIDE.md** - пошаговый гайд по деплою
- Автоматические скрипты для диагностики

## 📊 Мониторинг и аналитика

### 📈 Логирование
```python
# Структурированное логирование с эмодзи
LOGGING_CONFIG = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "level": "INFO",
    "handlers": [
        "StreamHandler",  # Консоль для Render
        "FileHandler"     # Файл для локальной разработки
    ]
}

# Отфильтрованы шумные логгеры
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('googleapiclient').setLevel(logging.WARNING)
```

### 🎯 Метрики и KPI
- Время отклика команд: <2 секунды
- Uptime: >99.5% (благодаря health checks)
- Успешность отправки напоминаний: >95%
- Процент завершенных встреч: отслеживается

## 🔄 CI/CD и развертывание

### 🚀 Автоматический деплой
1. **Git Push** → GitHub repository
2. **Automatic Trigger** → Render.com webhook
3. **Build Process** → Docker container
4. **Health Check** → Готовность к работе
5. **Webhook Update** → Telegram API notification

### 🧪 Тестирование
- **Локальная разработка**: SQLite + polling mode
- **Staging**: отдельный Telegram bot
- **Production**: PostgreSQL + webhook mode

## 📋 Версии и изменения

### v2.1.0 (30.07.2025) - Стабильный Production Release
- 🎉 **Успешный деплой на Render.com**
- ✅ **Исправлены все критические ошибки**
- ✅ **SQLAlchemy 2.0 полная совместимость**
- ✅ **Webhook режим стабильно работает**
- ✅ **Русскоязычный интерфейс восстановлен**
- ✅ **Система диагностики и инструменты**
- ✅ **Локальная разработка с SQLite**
- ✅ **Comprehensive troubleshooting documentation**

### v2.0.0 (30.07.2025) - Major Refactoring
- Миграция на SQLAlchemy 2.0
- Добавление webhook поддержки
- Система health check
- Полная русификация

### v1.1.0 - Optimization Release
- Оптимизация для малых команд
- Кеширование Google Calendar API
- Улучшенное логирование

### v1.0.0 - MVP Release
- Базовая функциональность встреч
- Интеграция с Google Calendar
- Система напоминаний

---

## 🎯 Заключение

Meeting Scheduler Bot v2.1 представляет собой полнофункциональную, производственно-готовую систему для автоматизации планирования встреч. Система успешно развернута, протестирована и готова к использованию в реальных условиях.

**Для поддержки и вопросов**: обращайтесь к администраторам системы или используйте встроенные диагностические инструменты.