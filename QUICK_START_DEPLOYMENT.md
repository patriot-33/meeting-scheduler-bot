# ⚡ БЫСТРЫЙ СТАРТ - Деплой за 5 минут

## 🚨 КРИТИЧЕСКИ ВАЖНО - СНАЧАЛА BACKUP!

```bash
cd /Users/evgenii/meeting-scheduler-bot/src
source ../venv/bin/activate
python ../backup_data.py
```
**Сохраните файл `data_backup_XXXXXXXX_XXXXXX.json` в безопасном месте!**

---

## 🚀 1. Подготовка к деплою (1 минута)

### GitHub:
1. Commit и push все изменения
2. Убедитесь что `service_account_key.json` в репозитории

### Render.com:
1. Создайте новый Web Service  
2. Подключите GitHub репозиторий
3. Выберите: **Docker** runtime

---

## 🔧 2. Environment Variables в Render.com (2 минуты)

Вставьте эти переменные в Render Dashboard:

```
TELEGRAM_BOT_TOKEN=8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec
ADMIN_TELEGRAM_IDS=99006770
GOOGLE_CALENDAR_ID_1=plantatorbob@gmail.com
GOOGLE_CALENDAR_ID_2=plantatorbob@gmail.com
WEBHOOK_URL=https://YOUR-APP-NAME.onrender.com
DEBUG=false
LOG_LEVEL=INFO
FORCE_ENUM_HOTFIX=true
```

**Замените `YOUR-APP-NAME` на реальное название вашего приложения!**

---

## 📚 3. Database Setup (автоматически)

Render.com автоматически:
- Создаст PostgreSQL базу данных
- Установит `DATABASE_URL`  
- Подключит к вашему приложению

---

## ▶️ 4. Запуск деплоя (1 минута)

1. Нажмите **"Create Web Service"**
2. Дождитесь зеленого статуса "Live"
3. Проверьте логи на отсутствие ошибок

---

## ✅ 5. Проверка работы (1 минута)

Откройте Telegram и протестируйте:
```
/start - должен ответить приветствием
/admin - должно открыться меню админа  
```

Если есть ошибки - проверьте логи в Render Dashboard.

---

## 🔄 6. Восстановление данных (ОБЯЗАТЕЛЬНО!)

После успешного деплоя восстановите данные:

### Через Render Console:
1. Зайдите в Render Dashboard → ваш сервис → Shell
2. Загрузите backup файл
3. Запустите: `python restore_data.py data_backup_XXXXXXXX_XXXXXX.json`

### Или локально с production DB:
```bash
# Скачайте backup файл на сервер и запустите restore
python restore_data.py data_backup_XXXXXXXX_XXXXXX.json
```

---

## 🎉 Готово!

Бот должен работать со всеми восстановленными данными:
- ✅ Пользователи восстановлены
- ✅ Слоты владельцев настроены  
- ✅ Админ имеет доступ
- ✅ Google Calendar подключен

---

## 🆘 Если что-то пошло не так:

1. **Бот не отвечает**: Проверьте TELEGRAM_BOT_TOKEN
2. **База данных ошибки**: Проверьте DATABASE_URL подключение
3. **Google Calendar не работает**: Проверьте service_account_key.json
4. **Webhook ошибки**: Проверьте WEBHOOK_URL правильность

**В крайнем случае**: Restart сервиса в Render Dashboard

---

**⏱️ Общее время деплоя: 5-10 минут**  
**🔄 Время восстановления данных: 2-3 минуты**

*Готово к продакшену!* 🚀