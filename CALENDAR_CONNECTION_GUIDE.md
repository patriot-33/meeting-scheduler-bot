# 🗓️ Руководство по подключению Google Calendar для руководителей

## 🎯 ПРОБЛЕМА И РЕШЕНИЕ

**Проблема:** Текущий OAuth требует централизованной настройки администратором
**Решение:** 3 альтернативных метода для самостоятельного подключения

---

## 📋 МЕТОД 1: Простое подключение через Calendar ID (Рекомендуется)

### ✅ Преимущества:
- Не требует OAuth авторизации
- Работает немедленно
- Полный контроль доступа у руководителя
- Поддержка корпоративных календарей

### 📝 Инструкция:

1. **Получите email сервисного аккаунта бота**
   ```
   /calendar_simple
   ```
   Бот покажет email вида: `bot-name@project-id.iam.gserviceaccount.com`

2. **Откройте Google Calendar**
   - Перейдите на https://calendar.google.com
   - Найдите нужный календарь в левой панели

3. **Поделитесь календарем с ботом**
   - Нажмите 3 точки рядом с календарем → "Настройки и общий доступ"
   - В разделе "Предоставить доступ определенным пользователям" нажмите "+ Добавить"
   - Вставьте email сервисного аккаунта
   - Выберите разрешение: "Вносить изменения"
   - Нажмите "Отправить"

4. **Скопируйте Calendar ID**
   - В настройках календаря прокрутите до раздела "Интеграция"
   - Скопируйте "Идентификатор календаря" (выглядит как `your.email@gmail.com`)

5. **Отправьте ID боту**
   ```
   /setcalendar your.email@gmail.com
   ```

### 🔒 Безопасность:
- Бот получает доступ только к указанному календарю
- Вы можете отозвать доступ в любой момент через настройки календаря
- Никаких паролей или токенов не передается

---

## 📋 МЕТОД 2: Device Code Flow (Без редиректов)

### ✅ Преимущества:
- Официальный OAuth без client_secret
- Не требует webhook/redirect
- Идеально для Telegram ботов

### 📝 Инструкция:

1. **Запросите код устройства**
   ```
   /calendar_device
   ```

2. **Бот выдаст:**
   - Ссылку: https://www.google.com/device
   - Код: XXXX-XXXX

3. **Авторизуйтесь:**
   - Откройте ссылку
   - Введите код
   - Войдите в Google аккаунт
   - Разрешите доступ к календарю

4. **Вернитесь в бот**
   - Бот автоматически определит успешную авторизацию
   - Календарь будет подключен

### 🔧 Техническая реализация:
```python
# В oauth_public_service.py
device_data = public_oauth_service.generate_device_code_url(user_id)
# Периодический polling для проверки авторизации
result = public_oauth_service.poll_device_code(user_id, device_code)
```

---

## 📋 МЕТОД 3: Публичный OAuth Client

### ✅ Преимущества:
- Не требует client_secret
- Использует публичный Client ID
- Подходит для open-source проектов

### 📝 Настройка администратором:

1. **Google Cloud Console:**
   - Создайте OAuth 2.0 Client ID
   - Тип: "Web application" или "TVs and Limited Input devices"
   - Добавьте redirect URI

2. **Добавьте в переменные окружения:**
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
   ```

3. **Руководители смогут:**
   ```
   /calendar_oauth
   ```
   И пройти стандартную OAuth авторизацию

---

## 🤔 КАКОЙ МЕТОД ВЫБРАТЬ?

### Для быстрого старта:
**Метод 1 (Calendar ID)** - самый простой, работает сразу

### Для максимальной безопасности:
**Метод 2 (Device Code)** - официальный OAuth без секретов

### Для масштабирования:
**Метод 3 (Public OAuth)** - стандартный подход для публичных приложений

---

## 🛠️ ИНТЕГРАЦИЯ В КОД

### Добавьте в main.py:
```python
# Простое подключение через Calendar ID
from handlers.manager_calendar_simple import (
    simple_calendar_connect, 
    set_calendar_id,
    simple_calendar_faq
)

# Device Code Flow
from services.oauth_public_service import public_oauth_service

# Регистрация команд
application.add_handler(CommandHandler("calendar_simple", simple_calendar_connect))
application.add_handler(CommandHandler("setcalendar", set_calendar_id))
application.add_handler(CallbackQueryHandler(simple_calendar_faq, pattern="^simple_calendar_faq$"))
```

### Обновите меню бота:
```python
keyboard = [
    [InlineKeyboardButton("🔗 OAuth подключение", callback_data="oauth_calendar")],
    [InlineKeyboardButton("📅 Простое подключение", callback_data="simple_calendar")],
    [InlineKeyboardButton("📱 Device Code", callback_data="device_calendar")]
]
```

---

## ❓ FAQ

**Q: Можно ли подключить несколько календарей?**
A: В текущей версии - один основной календарь на руководителя

**Q: Работает ли с Google Workspace?**
A: Да, все методы поддерживают корпоративные аккаунты

**Q: Как сменить календарь?**
A: Просто выполните `/setcalendar` с новым ID

**Q: Бот видит личные данные?**
A: Только события в календаре, к которому вы дали доступ

---

## 🚀 РЕЗУЛЬТАТ

После подключения любым методом руководитель получает:
- ✅ Автоматическое создание встреч в своем календаре
- ✅ Google Meet ссылки для видеоконференций  
- ✅ Синхронизацию с личным расписанием
- ✅ Уведомления о встречах

Больше не нужно ждать администратора для настройки OAuth! 🎉