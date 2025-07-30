# 🚀 Руководство по деплою на Render.com

## 🔧 Шаги для восстановления сервиса

### 1. Зайдите в Render Dashboard
- Откройте https://dashboard.render.com
- Войдите в аккаунт
- Найдите сервис `meeting-scheduler-bot-fkp8`

### 2. Проверьте статус сервиса
Возможные статусы:
- 🟢 **Live** - сервис работает
- 🟡 **Building** - сервис деплоится
- 🔴 **Failed** - ошибка деплоя
- ⭕ **Suspended** - сервис приостановлен

### 3. Если сервис в статусе "Failed"
1. Перейдите в раздел **Logs**
2. Найдите ошибки в последних логах
3. Нажмите **Manual Deploy** → **Deploy latest commit**
4. Дождитесь завершения деплоя (5-10 минут)

### 4. Проверьте переменные окружения
Убедитесь, что установлены:
```
TELEGRAM_BOT_TOKEN=8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec
ADMIN_TELEGRAM_IDS=99006770
WEBHOOK_URL=https://meeting-scheduler-bot-fkp8.onrender.com
WEBHOOK_PATH=/webhook
PORT=10000
DATABASE_URL=(автоматически от Render)
GOOGLE_CALENDAR_ID_1=test@gmail.com
GOOGLE_CALENDAR_ID_2=test@gmail.com
```

### 5. Проверьте базу данных
- В разделе **Databases** должна быть база `meeting-scheduler-db`
- Статус должен быть **Available**

### 6. После успешного деплоя
Запустите скрипт настройки webhook:
```bash
python3 deploy_to_render.py
```

## 🐛 Частые проблемы и решения

### Проблема: "Build failed"
**Решение:** 
1. Проверьте логи сборки
2. Возможно, не хватает зависимостей
3. Попробуйте Clear Build Cache → Manual Deploy

### Проблема: "Application error"
**Решение:**
1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения установлены
3. Проверьте подключение к базе данных

### Проблема: "Timeout/503 Error"
**Решение:**
1. Сервис может долго запускаться (cold start)
2. Подождите 2-3 минуты
3. Проверьте метрики CPU/Memory в Dashboard

### Проблема: "Database connection error"
**Решение:**
1. Проверьте статус PostgreSQL базы
2. Убедитесь, что DATABASE_URL правильный
3. Возможно, нужно Restart базы данных

## 📞 После успешного деплоя

1. ✅ Сервис показывает статус **Live**
2. ✅ URL `https://meeting-scheduler-bot-fkp8.onrender.com/health` отвечает
3. ✅ Webhook настроен командой `python3 deploy_to_render.py`
4. ✅ Бот отвечает в Telegram на команды

## 🎯 Быстрый чек-лист

- [ ] Render сервис в статусе Live
- [ ] База данных Available  
- [ ] Переменные окружения установлены
- [ ] Webhook настроен
- [ ] Бот отвечает на /start в Telegram

## 🔄 Альтернативный план

Если Render не работает, можно:
1. Использовать `run_simple_bot.py` для локального запуска
2. Попробовать другой hosting (Heroku, Railway, Fly.io)
3. Использовать VPS с Docker

---

**Важно:** После каждого изменения кода делайте git push, Render автоматически переразвернет сервис.