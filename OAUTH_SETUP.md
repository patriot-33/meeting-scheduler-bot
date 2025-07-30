# 🔧 Настройка Google OAuth Client для Meeting Scheduler Bot

## 🚨 КРИТИЧЕСКАЯ ОШИБКА ИСПРАВЛЕНА

**Проблема:** `Client secrets must be for a web or installed app`
**Причина:** Система использовала Service Account JSON для OAuth flow
**Решение:** Добавлен отдельный OAuth Client JSON

---

## 📋 ШАГ 1: Google Cloud Console

### 1.1 Перейдите в Google Cloud Console
- Откройте https://console.cloud.google.com/
- Выберите ваш проект (или создайте новый)

### 1.2 Включите API
- Перейдите в **APIs & Services** → **Library**
- Найдите и включите:
  - **Google Calendar API**
  - **Google Meet API** (опционально)

### 1.3 Создайте OAuth 2.0 Client
- Перейдите в **APIs & Services** → **Credentials**
- Нажмите **+ CREATE CREDENTIALS** → **OAuth 2.0 Client IDs**
- Выберите **Application type: Web application**
- Укажите **Name**: `Meeting Scheduler Bot OAuth`

### 1.4 Настройте Redirect URIs
```
Authorized redirect URIs:
https://your-bot-domain.com/oauth/callback
https://meeting-scheduler-bot-fkp8.onrender.com/oauth/callback
```

### 1.5 Скачайте JSON
- Нажмите **DOWNLOAD JSON**
- Сохраните файл как `oauth_client_key.json`

---

## 📋 ШАГ 2: Конфигурация в коде

### Вариант A: Environment Variable (Рекомендуется для продакшена)
```bash
export GOOGLE_OAUTH_CLIENT_JSON='{"web":{"client_id":"...","client_secret":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","redirect_uris":["https://your-domain.com/oauth/callback"]}}'
```

### Вариант B: Файл (Для разработки)
```bash
# Поместите oauth_client_key.json в корень проекта
cp downloaded_oauth_client.json /path/to/meeting-scheduler-bot/oauth_client_key.json
```

---

## 📋 ШАГ 3: Проверка конфигурации

### 3.1 Структура OAuth Client JSON
```json
{
  "web": {
    "client_id": "123456789-abcdefg.apps.googleusercontent.com",
    "project_id": "your-project-id", 
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-...",
    "redirect_uris": [
      "https://your-domain.com/oauth/callback"
    ]
  }
}
```

### 3.2 Переменные окружения
```bash
# Обязательные для OAuth
WEBHOOK_URL=https://your-domain.com
GOOGLE_OAUTH_CLIENT_JSON='{...}'  # или файл oauth_client_key.json

# Дополнительные (остались без изменений)
GOOGLE_SERVICE_ACCOUNT_JSON='{...}'  # Для owner календаря
TELEGRAM_BOT_TOKEN=your_bot_token
DATABASE_URL=your_database_url
```

---

## 📋 ШАГ 4: Тестирование

### 4.1 Запуск бота
```bash
cd meeting-scheduler-bot
python src/main.py
```

### 4.2 Проверка логов
```bash
# Должно появиться:
INFO - OAuth Client configuration: validated
INFO - Generated OAuth URL for manager 123456789

# НЕ должно быть:
ERROR - Client secrets must be for a web or installed app
ERROR - Google service account JSON not configured
```

### 4.3 Тестирование через Telegram
1. Отправьте команду `/calendar` в бот
2. Нажмите "🔗 Подключить Google Calendar"
3. Должна открыться страница авторизации Google
4. После авторизации - возврат в бот с подтверждением

---

## 🛡️ БЕЗОПАСНОСТЬ

### ❌ НЕ ДЕЛАЙТЕ:
- Не коммитьте OAuth Client JSON в Git
- Не используйте Service Account для OAuth
- Не устанавливайте слишком широкие scopes

### ✅ ДЕЛАЙТЕ: 
- Используйте переменные окружения
- Ограничьте redirect URIs
- Регулярно проверяйте доступ в Google Console

---

## 🔍 TROUBLESHOOTING

### Ошибка: "Client secrets must be for a web or installed app"
**Решение:** Используйте OAuth Client JSON, а не Service Account JSON

### Ошибка: "redirect_uri_mismatch"
**Решение:** Добавьте точный URI в Google Console Credentials

### Ошибка: "invalid_grant" 
**Решение:** Проверьте правильность client_secret и redirect_uri

### Ошибка: "OAuth Client не настроен"
**Решение:** Установите GOOGLE_OAUTH_CLIENT_JSON или создайте oauth_client_key.json

---

## 📞 ПОДДЕРЖКА

При проблемах проверьте:
1. Логи приложения: `tail -f logs/app.log`
2. Конфигурацию: `/config_summary` в боте
3. OAuth Client в Google Console
4. Переменные окружения: `env | grep GOOGLE`

---

## 🎉 РЕЗУЛЬТАТ

После настройки:
- ✅ Менеджеры могут подключать свои Google Calendar
- ✅ Автоматическое создание встреч с Google Meet
- ✅ Приглашения участников через email
- ✅ Синхронизация с личными календарями

**Архитектура:**
- **Service Account** → Owner календарь (создание встреч)
- **OAuth Client** → Manager календари (личная синхронизация)