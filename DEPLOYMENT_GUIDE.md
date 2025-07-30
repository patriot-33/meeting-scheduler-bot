# 🚀 Meeting Scheduler Bot - Deployment Guide

## 📋 Полный аудит и исправления

### ❌ Исправленные критические ошибки:

1. **AttributeError: handle_booking_callback не существует**
   - ✅ Удален вызов несуществующей функции `manager.handle_booking_callback`
   - ✅ Исправлена архитектура обработчиков в `main.py`

2. **PTBUserWarning в ConversationHandler**
   - ✅ Удален `per_message=True` из ConversationHandler в `registration.py`
   - ✅ Удален `per_message=True` из ConversationHandler в `owner.py`

3. **Отсутствующий health check endpoint**
   - ✅ Добавлен `/health` endpoint в webhook server
   - ✅ Интегрирована функция health_check в main.py

4. **Несовместимость environment variables**
   - ✅ Исправлена переменная `TELEGRAM_TOKEN` → `TELEGRAM_BOT_TOKEN` в render.yaml
   - ✅ Добавлена обратная совместимость в config.py

5. **Строгая валидация конфигурации**
   - ✅ Исправлены validators для разработки/тестирования
   - ✅ Добавлены default значения для обязательных полей

## 🛠 Инструкция по деплою на Render.com

### 1. Подготовка проекта

```bash
# Клонировать исправленный проект
git clone https://github.com/patriot-33/meeting-scheduler-bot.git
cd meeting-scheduler-bot

# Проверить структуру проекта
ls -la
# Должны быть: src/, requirements.txt, Dockerfile, render.yaml
```

### 2. Настройка на Render.com

1. **Создание нового Web Service**
   - Зайти в [Render Dashboard](https://dashboard.render.com)
   - New → Web Service
   - Connect Repository: `https://github.com/patriot-33/meeting-scheduler-bot`

2. **Настройки сервиса**
   ```yaml
   Name: meeting-scheduler-bot
   Runtime: Docker
   Build Command: pip install -r requirements.txt
   Start Command: cd src && python main.py
   ```

3. **Environment Variables (ОБЯЗАТЕЛЬНО!)**
   ```bash
   # Telegram Bot
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   
   # Admin IDs (ваши Telegram ID)
   ADMIN_TELEGRAM_IDS=123456789,987654321
   
   # Google Calendar
   GOOGLE_CALENDAR_ID_1=primary
   GOOGLE_CALENDAR_ID_2=your-second-calendar@group.calendar.google.com
   
   # Google Service Account (весь JSON как одна строка!)
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
   
   # Production settings
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   WEBHOOK_URL=https://your-app-name.onrender.com
   ```

### 3. Создание PostgreSQL базы данных

1. **В Render Dashboard**
   - New → PostgreSQL
   - Name: `meeting-scheduler-db`
   - Plan: Free
   
2. **Подключение к Web Service**
   - В настройках Web Service
   - Environment Variables → Add from Database
   - Select: `meeting-scheduler-db`
   - Variable: `DATABASE_URL`

### 4. Получение Telegram Bot Token

```bash
# 1. Создать бота через @BotFather в Telegram
# 2. Отправить команду: /newbot
# 3. Следовать инструкциям
# 4. Получить токен формата: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 5. Настройка Google Calendar API

1. **Google Cloud Console**
   - Перейти в [Google Cloud Console](https://console.cloud.google.com)
   - Создать новый проект или выбрать существующий
   - Включить Google Calendar API

2. **Service Account**
   ```bash
   # 1. IAM & Admin → Service Accounts
   # 2. Create Service Account
   # 3. Download JSON key file
   # 4. Скопировать весь JSON в переменную GOOGLE_SERVICE_ACCOUNT_JSON
   ```

3. **Настройка календаря**
   - Поделиться календарем с email из Service Account
   - Дать права на изменение событий

## ✅ Checklist после деплоя

### Проверки сразу после деплоя:

- [ ] ✅ Сервис запустился без ошибок
- [ ] ✅ Health check доступен: `https://your-app.onrender.com/health`
- [ ] ✅ База данных подключена (статус "healthy")
- [ ] ✅ Логи не содержат критических ошибок
- [ ] ✅ Бот отвечает на команду `/start`

### Функциональные тесты:

- [ ] ✅ Регистрация нового пользователя: `/register`
- [ ] ✅ Админ панель работает: `/admin`
- [ ] ✅ Owner панель работает: `/owner`
- [ ] ✅ Создание слотов владельцем
- [ ] ✅ Бронирование встреч менеджером: `/schedule`
- [ ] ✅ Google Calendar интеграция работает
- [ ] ✅ Отправка email уведомлений

## 🐛 Диагностика проблем

### Если бот не запускается:

1. **Проверить логи**
   ```bash
   # В Render Dashboard → Logs
   # Ищем ошибки типа:
   # - "AttributeError"
   # - "Database connection failed"
   # - "Invalid token"
   ```

2. **Частые проблемы и решения**
   ```bash
   # Ошибка: "telegram_bot_token validation error"
   # Решение: Проверить переменную TELEGRAM_BOT_TOKEN
   
   # Ошибка: "Database connection failed"
   # Решение: Проверить подключение DATABASE_URL
   
   # Ошибка: "Google Calendar not available"
   # Решение: Проверить GOOGLE_SERVICE_ACCOUNT_JSON
   ```

### Health Check коды ответов:

- **200 OK**: Все системы работают
- **503 Service Unavailable**: Проблемы с БД или конфигурацией

### Monitoring команды:

```bash
# Проверка статуса
curl https://your-app.onrender.com/health

# Результат должен быть:
{
  "status": "healthy",
  "checks": {
    "database": {"status": true, "message": "Database OK"},
    "config": {"status": true, "message": "Config OK"}
  }
}
```

## 🔧 Troubleshooting

### Проблема: "ConversationHandler per_message warning"
**Статус**: ✅ ИСПРАВЛЕНО
- Удален параметр `per_message=True` из всех ConversationHandler

### Проблема: "handle_booking_callback not found"
**Статус**: ✅ ИСПРАВЛЕНО  
- Удалены вызовы несуществующих функций в main.py
- Исправлена архитектура обработчиков

### Проблема: "Health check endpoint missing"
**Статус**: ✅ ИСПРАВЛЕНО
- Добавлен `/health` endpoint в webhook server
- Интегрирован health_check.py

## 📞 Техническая поддержка

При возникновении проблем:

1. **Проверить логи** в Render Dashboard
2. **Убедиться** что все environment variables установлены
3. **Проверить** health check endpoint
4. **Связаться** с администратором проекта

---

## 🎉 Успешный деплой!

После выполнения всех шагов бот должен:
- ✅ Запускаться без ошибок
- ✅ Принимать команды в Telegram
- ✅ Создавать встречи в Google Calendar
- ✅ Отправлять уведомления пользователям

**Время деплоя**: ~10-15 минут  
**Требования**: Telegram Bot Token, Google Service Account, PostgreSQL  
**Поддерживаемые платформы**: Render.com, Vercel, Railway, любой Docker-хостинг