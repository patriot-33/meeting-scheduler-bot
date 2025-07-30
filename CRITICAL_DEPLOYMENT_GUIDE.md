# 🚨 КРИТИЧЕСКОЕ РУКОВОДСТВО ПО ДЕПЛОЮ 

## ⚠️ ВНИМАНИЕ: ПОТЕРЯ ДАННЫХ

**КРИТИЧЕСКАЯ ПРОБЛЕМА**: При деплое на Render.com произойдет переход с SQLite на PostgreSQL, что приведет к **ПОЛНОЙ ПОТЕРЕ ВСЕХ ДАННЫХ**:

- ❌ Все одобренные руководители будут удалены
- ❌ Настроенные временные слоты исчезнут  
- ❌ История встреч будет потеряна
- ❌ Статистика пользователей обнулится

## 🛡️ РЕШЕНИЕ: Обязательная процедура Backup/Restore

### ШАГ 1: Создание Backup ДО деплоя

```bash
# В локальной среде, ДО деплоя на Render.com
cd /Users/evgenii/meeting-scheduler-bot
source venv/bin/activate
python backup_data.py
```

Это создаст файл `data_backup_YYYYMMDD_HHMMSS.json` с ВСЕМИ важными данными.

### ШАГ 2: Деплой на Render.com

1. Загрузите код на GitHub
2. Подключите репозиторий к Render.com
3. Настройте environment variables
4. Дождитесь успешного деплоя

### ШАГ 3: Восстановление данных ПОСЛЕ деплоя

```bash
# На сервере Render.com или через локальный скрипт с production DB
python restore_data.py data_backup_YYYYMMDD_HHMMSS.json
```

## 🔧 Environment Variables для Production

Установите в Render.com:

```bash
TELEGRAM_BOT_TOKEN=8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec
ADMIN_TELEGRAM_IDS=99006770
DATABASE_URL=[автоматически устанавливается Render.com]
GOOGLE_CALENDAR_ID_1=plantatorbob@gmail.com
GOOGLE_CALENDAR_ID_2=plantatorbob@gmail.com
WEBHOOK_URL=https://your-app-name.onrender.com
DEBUG=false
LOG_LEVEL=INFO
FORCE_ENUM_HOTFIX=true
```

## 📋 Чек-лист перед деплоем

### Обязательные действия:
- [ ] Запустить `python backup_data.py` 
- [ ] Сохранить файл backup в безопасном месте
- [ ] Загрузить `service_account_key.json` в репозиторий
- [ ] Настроить environment variables в Render.com
- [ ] Протестировать деплой

### После деплоя:
- [ ] Запустить `python restore_data.py backup_file.json`
- [ ] Проверить, что пользователи восстановлены
- [ ] Проверить, что слоты владельцев восстановлены  
- [ ] Протестировать функционал бота
- [ ] Проверить интеграцию с Google Calendar

## 🚨 Альтернативная стратегия: Manual Recreation

Если backup/restore не сработает, нужно будет вручную:

1. **Пересоздать пользователей**:
   - Каждый пользователь заново пройдет регистрацию через `/start`
   - Админ одобрит пользователей через `/admin`

2. **Восстановить слоты владельцев**:
   - Владелец зайдет в `/owner`
   - Настроит доступные временные слоты заново

3. **Переназначить роли**:
   - Через админ-панель `/admin` назначить роли пользователям

## 📞 Экстренные контакты для восстановления

**Telegram ID владельца/админа**: 99006770
**Google Calendar**: plantatorbob@gmail.com

## 🔍 Мониторинг после деплоя

Проверьте в течение 24 часов:

1. **Бот отвечает на команды**: `/start`, `/help`
2. **Админ-функции работают**: `/admin`, `/users`
3. **Регистрация работает**: новые пользователи могут зарегистрироваться
4. **Владелец может настроить слоты**: `/owner` 
5. **Интеграция с Google Calendar**: создание встреч
6. **Уведомления приходят**: проверить напоминания

## ⚡ Быстрое восстановление после проблем

Если что-то пошло не так:

```bash
# 1. Проверить логи в Render.com Dashboard
# 2. Проверить environment variables
# 3. Перезапустить сервис в Render.com
# 4. При необходимости - rollback и повторный деплой
```

## 🛠️ Готовые скрипты

В проекте созданы:
- ✅ `backup_data.py` - экспорт данных
- ✅ `restore_data.py` - импорт данных  
- ✅ `comprehensive_audit.py` - полная проверка
- ✅ Обновленные `Dockerfile` и `render.yaml`

---

**ВАЖНО**: Не игнорируйте процедуру backup! Восстановить данные после деплоя без backup будет невозможно.