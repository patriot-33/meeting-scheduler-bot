# 🚀 ИНСТРУКЦИИ ПО ДЕПЛОЮ

## 📋 БЫСТРЫЙ СТАРТ

### 1. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database Configuration (Render PostgreSQL)  
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google Calendar Configuration
GOOGLE_CALENDAR_ID_1=your_email@gmail.com
GOOGLE_CALENDAR_ID_2=partner_email@gmail.com

# Admin Configuration (ваши Telegram ID)
ADMIN_TELEGRAM_IDS=123456789,987654321

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
FORCE_ENUM_HOTFIX=True
```

### 2. Деплой на Render.com

1. **Создайте новый Web Service в Render.com:**
   - Repository: https://github.com/patriot-33/meeting-scheduler-bot
   - Branch: main
   - Runtime: Docker

2. **Создайте PostgreSQL базу данных:**
   - Plan: Free
   - Database Name: meeting_scheduler
   - User: meeting_bot

3. **Настройте Environment Variables в Render:**
   ```
   DATABASE_URL -> from database (connection string)
   TELEGRAM_BOT_TOKEN -> ваш токен бота
   ADMIN_TELEGRAM_IDS -> ваши Telegram ID через запятую
   GOOGLE_CALENDAR_ID_1 -> первый календарь  
   GOOGLE_CALENDAR_ID_2 -> второй календарь
   PORT -> 8443
   FORCE_ENUM_HOTFIX -> true
   ```

4. **Deploy и проверка:**
   - Нажмите "Deploy"
   - Дождитесь завершения деплоя
   - Проверьте логи на наличие ошибок

## ✅ ЧЕКЛИСТ ПРОВЕРОК ПОСЛЕ ДЕПЛОЯ

### Сразу после деплоя:
- [ ] Деплой завершился без ошибок
- [ ] База данных подключена и инициализирована  
- [ ] В логах есть сообщение "✅ Database initialized"
- [ ] В логах есть сообщение "✅ Scheduler started"
- [ ] Health check endpoint `/health` возвращает 200

### Функциональное тестирование:
- [ ] Бот отвечает на команду `/start`
- [ ] Владелец автоматически регистрируется при первом `/start`
- [ ] Команда `/owner` открывает панель владельца
- [ ] Кнопка "📅 Управление доступностью" работает
- [ ] Кнопка "➕ Добавить слот" работает  
- [ ] Кнопка "📝 Настроить день полностью" работает
- [ ] Кнопка "🔄 Обновить расписание" работает
- [ ] После команды `/start` настройки слотов сохраняются

## 🐛 УСТРАНЕНИЕ НЕПОЛАДОК

### Ошибка "Database connection failed"
```bash
# Проверьте DATABASE_URL
echo $DATABASE_URL
# Должен начинаться с postgresql://
```

### Ошибка "Enum type does not exist"
```bash
# Убедитесь что установлено:
FORCE_ENUM_HOTFIX=true
```

### Бот не отвечает на команды
```bash
# Проверьте токен бота
echo $TELEGRAM_BOT_TOKEN
# Проверьте что бот активен в @BotFather
```

### Ошибка "Вы не зарегистрированы как владелец"
```bash
# Проверьте ADMIN_TELEGRAM_IDS
echo $ADMIN_TELEGRAM_IDS  
# Должен содержать ваш реальный Telegram ID
```

## 🔄 ОБНОВЛЕНИЕ ДЕПЛОЯ

1. **Автоматическое обновление:**
   - Push в main branch → автоматический redeploy

2. **Ручное обновление:**
   - Render Dashboard → Manual Deploy → "Deploy latest commit"

3. **Откат к предыдущей версии:**
   - Render Dashboard → Deploys → Select previous deploy → Redeploy

## 📊 МОНИТОРИНГ

### Логи для проверки:
```bash
# Успешный запуск
"🚀 Starting Meeting Scheduler Bot for team..."
"✅ Database initialized"  
"✅ Scheduler started"

# Ошибки для внимания
"❌ Database initialization failed"
"❌ Scheduler setup failed"
"Database error occurred"
```

### Health Check:
```bash
curl https://your-app.onrender.com/health
# Должен вернуть: {"status": "healthy", "timestamp": "..."}
```

## 🎯 ПРОВЕРКА КЛЮЧЕВОЙ ФУНКЦИОНАЛЬНОСТИ

После деплоя обязательно проверьте исправленные баги:

1. **Тест распознавания владельца:**
   - Отправьте `/start` → должно быть приветствие владельца
   - Отправьте `/owner` → должна открыться панель

2. **Тест сохранения состояния:**
   - Настройте слоты через "Управление доступностью"
   - Отправьте `/start`
   - Проверьте что слоты остались на месте

3. **Тест кнопок:**
   - Нажмите "➕ Добавить слот" → должен открыться выбор дня
   - Нажмите "📝 Настроить день полностью" → должна открыться настройка
   - Нажмите "🔄 Обновить расписание" → должно обновиться

## 🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ

Если что-то пошло не так:

1. **Быстрый откат:**
   ```bash
   # В Render Dashboard
   Deploys → Previous working deploy → Redeploy
   ```

2. **Сброс базы данных:**
   ```bash
   # В PostgreSQL Dashboard  
   Drop all tables → Redeploy app
   ```

3. **Проверка переменных:**
   ```bash
   # Environment Variables в Render
   Убедитесь что все переменные из .env.example заполнены
   ```

---

**⚡ РЕЗУЛЬТАТ:** После выполнения этих инструкций бот будет работать стабильно без ошибок!