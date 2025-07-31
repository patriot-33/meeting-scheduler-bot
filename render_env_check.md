# 🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: OAuth не работает на Render.com

## Диагностика показала:
- ✅ Локально OAuth Service работает
- ❌ На Render.com получаем "Проблема с подключением"
- ❌ Переменные окружения не видны в диагностике

## СРОЧНО ПРОВЕРИТЬ НА RENDER.COM:

### 1. Зайдите в Dashboard Render.com
- Откройте ваш сервис meeting-scheduler-bot
- Перейдите в Settings → Environment

### 2. Проверьте наличие переменной GOOGLE_OAUTH_CLIENT_JSON
**Должна быть установлена ТОЧНО так:**

```
GOOGLE_OAUTH_CLIENT_JSON={"web":{"client_id":"YOUR_CLIENT_ID","project_id":"meeting-scheduler-bot-467415","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR_CLIENT_SECRET","redirect_uris":["https://meeting-scheduler-bot-fkp8.onrender.com/oauth/callback"]}}
```

### 3. ВАЖНО: Формат переменной
- ❌ НЕ добавляйте пробелы после знака =
- ❌ НЕ переносите JSON на новые строки
- ✅ Вся строка должна быть одной линией
- ✅ Все кавычки должны быть экранированы правильно

### 4. После добавления переменной:
1. Нажмите "Save Changes"
2. Дождитесь автоматического редеплоя (зеленый статус)
3. Протестируйте команду /calendar

## ПРОВЕРКА РЕЗУЛЬТАТА:
После исправления менеджер должен увидеть:
```
🔗 **Подключение Google Calendar**

Для автоматического создания встреч в вашем календаре:

1️⃣ **Нажмите "Подключить календарь"**
   • Вы перейдете на страницу авторизации Google
   • Войдите в ваш Google аккаунт
...

[🔗 Подключить Google Calendar] [❓ Частые вопросы] [← Назад]
```

Вместо: "Проблема с подключением. Попробуйте еще раз."

## АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ:
Если проблема сохраняется, добавьте также:
```
WEBHOOK_URL=https://meeting-scheduler-bot-fkp8.onrender.com
```