# 🔧 Решение проблем с Meeting Scheduler Bot

## ❌ Бот не отвечает на команды

### 1. Проверьте webhook настройки

```bash
python3 check_webhook.py
```

Этот скрипт покажет:
- Текущий webhook URL
- Количество необработанных обновлений
- Последние ошибки

### 2. Проверьте работу бота

```bash
python3 test_bot.py
```

Этот скрипт:
- Проверит, что бот активен
- Покажет информацию о боте
- Позволит отправить тестовое сообщение

### 3. Установите команды бота

```bash
python3 setup_bot_commands.py
```

Это установит все команды в меню бота.

## 🔄 Переключение между Webhook и Polling

### Webhook режим (для production на Render)

1. Запустите `python3 check_webhook.py`
2. Выберите опцию 1 или 4 для установки webhook
3. URL должен быть: `https://meeting-scheduler-bot-fkp8.onrender.com/webhook`

### Polling режим (для локальной разработки)

1. Запустите `python3 check_webhook.py`
2. Выберите опцию 2 для удаления webhook
3. Запустите бота локально без WEBHOOK_URL в .env

## 🔍 Диагностика на Render.com

### Проверьте логи
1. Зайдите в Dashboard Render.com
2. Откройте ваш сервис
3. Перейдите в раздел "Logs"
4. Ищите ошибки или предупреждения

### Проверьте переменные окружения
Убедитесь, что установлены:
- `TELEGRAM_BOT_TOKEN` - токен вашего бота
- `ADMIN_TELEGRAM_IDS` - ID администраторов
- `WEBHOOK_URL` - https://meeting-scheduler-bot-fkp8.onrender.com
- `DATABASE_URL` - автоматически от Render

### Проверьте Health Check
```bash
curl https://meeting-scheduler-bot-fkp8.onrender.com/health
```

## 📝 Частые проблемы

### "Бот не реагирует на /start"

1. **Неправильный webhook URL**
   - Проверьте через `check_webhook.py`
   - Переустановите webhook (опция 4)

2. **Накопились необработанные обновления**
   - Удалите webhook (опция 2)
   - Проверьте обновления (опция 3)
   - Установите webhook заново (опция 1)

3. **Ошибка в коде обработчика**
   - Проверьте логи на Render
   - Ищите Python traceback

### "Webhook не устанавливается"

1. **Неверный токен бота**
   - Проверьте TELEGRAM_BOT_TOKEN
   - Получите новый токен у @BotFather

2. **Неверный URL**
   - URL должен быть HTTPS
   - Проверьте, что сервис запущен на Render

### "База данных не подключается"

1. **Проверьте DATABASE_URL**
   - Должен быть установлен автоматически Render
   - Формат: `postgresql://user:pass@host:port/dbname`

2. **Проверьте миграции**
   - База должна инициализироваться при запуске

## 🚨 Экстренные действия

### Полный перезапуск

1. Удалите webhook:
   ```bash
   python3 check_webhook.py
   # Выберите опцию 2
   ```

2. Перезапустите сервис на Render:
   - Dashboard → Service → Manual Deploy → Deploy latest commit

3. Дождитесь запуска и переустановите webhook:
   ```bash
   python3 check_webhook.py
   # Выберите опцию 1
   ```

### Проверка токена

Убедитесь, что токен правильный:
1. Откройте @BotFather
2. Отправьте `/mybot`
3. Выберите вашего бота
4. Нажмите "API Token"
5. Сравните с токеном в Render

## 📞 Контакты поддержки

Если проблема не решается, проверьте:
1. [Telegram Bot API документацию](https://core.telegram.org/bots/api)
2. [Render.com документацию](https://render.com/docs)
3. Логи приложения на Render Dashboard