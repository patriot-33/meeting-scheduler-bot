# Чеклист развертывания Meeting Scheduler Bot

## ✅ Обязательные Environment Variables в Render.com

### 🔑 Telegram конфигурация
```bash
TELEGRAM_BOT_TOKEN=8318735096:AAH...
ADMIN_TELEGRAM_IDS=99006770
WEBHOOK_URL=https://meeting-scheduler-bot-fkp8.onrender.com  # КРИТИЧНО!
```

### 🗄️ База данных
```bash
DATABASE_URL=postgresql://meeting_bot:...@dpg-...render.com/meeting_scheduler
```

### 📅 Google Calendar
```bash
GOOGLE_CALENDAR_ID_1=plantatorbob@gmail.com
GOOGLE_CALENDAR_ID_2=plantatorbob@gmail.com
GOOGLE_CALENDAR_ENABLED=true
```

### 🔐 Google Service Account (JSON)
```bash
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### 🔐 Google OAuth Client (JSON)
```bash
GOOGLE_OAUTH_CLIENT_JSON={"web":{"client_id":"...",...}}
```

### 🌍 Среда выполнения
```bash
ENVIRONMENT=production          # КРИТИЧНО!
LOG_LEVEL=DEBUG
TIMEZONE=Europe/Moscow
```

### 👥 Владельцы
```bash
EXPECTED_OWNERS_COUNT=1
ALLOW_SINGLE_OWNER_MODE=true
FALLBACK_MODE=true
```

## 🚨 Критические проверки перед развертыванием

### 1. Webhook конфигурация
- [ ] `WEBHOOK_URL` НЕ закомментирован
- [ ] `ENVIRONMENT=production`
- [ ] URL соответствует домену Render.com

### 2. Google Calendar настройка
- [ ] Service Account JSON корректен
- [ ] OAuth Client JSON корректен
- [ ] Redirect URI в OAuth = `https://meeting-scheduler-bot-fkp8.onrender.com/oauth/callback`

### 3. База данных
- [ ] DATABASE_URL активен
- [ ] Таблицы созданы (users, meetings, owner_availability)
- [ ] Миграции применены

### 4. Безопасность
- [ ] `.env` файл НЕ в git репозитории
- [ ] Все секреты в environment variables
- [ ] Admin IDs настроены корректно

## 🔍 Диагностика после развертывания

### Проверка webhook
```bash
curl -X POST https://meeting-scheduler-bot-fkp8.onrender.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

### Ожидаемые логи в Render.com
```
✅ Webhook set: https://meeting-scheduler-bot-fkp8.onrender.com
🔗 WEBHOOK STATUS: OK - No errors
📥 WEBHOOK: ========== NEW REQUEST ==========
🚑 EMERGENCY: create_meeting_in_both_calendars CALLED
```

### Проверка статуса Telegram webhook
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

## 🏗️ Последовательность развертывания

### 1. Подготовка
1. Убедиться что все изменения в Git
2. Проверить .env НЕ в репозитории
3. Подготовить environment variables

### 2. Настройка Render.com
1. Добавить все environment variables
2. Установить `WEBHOOK_URL` и `ENVIRONMENT=production`
3. Сохранить настройки

### 3. Развертывание
1. Push на GitHub (автодеплой)
2. Дождаться успешного build
3. Проверить логи запуска

### 4. Проверка функциональности
1. Отправить `/start` боту
2. Попробовать команду `/schedule`
3. Создать тестовую встречу
4. Проверить события в календарях

## 🆘 Решение проблем

### Webhook не работает
- Проверить `WEBHOOK_URL` не закомментирован
- Проверить `ENVIRONMENT=production`
- Перезапустить сервис в Render.com

### События не создаются
- Проверить логи `🚑 EMERGENCY`
- Проверить Google Service Account permissions
- Проверить OAuth client redirect URI

### База данных недоступна
- Проверить DATABASE_URL актуален
- Проверить подключение к PostgreSQL
- Выполнить миграции

## 📊 Мониторинг

### Ключевые метрики
- [ ] Webhook requests в минуту
- [ ] Successful calendar events created
- [ ] Google API rate limits
- [ ] Database connection health

### Алерты
- [ ] Webhook connection timeout
- [ ] Google API quota exceeded
- [ ] Database connection failed
- [ ] Bot polling conflicts

## 🔄 Резервное копирование

### Еженедельно
- [ ] Backup PostgreSQL database
- [ ] Export user configurations
- [ ] Archive diagnostic logs

### При критических изменениях
- [ ] Create rollback commit
- [ ] Document changes in CHANGELOG
- [ ] Test in staging environment

---

**⚠️ КРИТИЧНО:** Всегда проверяйте базовые компоненты (webhook, environment variables) перед диагностикой сложной логики!