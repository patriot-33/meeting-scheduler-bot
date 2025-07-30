#!/usr/bin/env python3
"""
Детальная диагностика проблем с ботом
"""
import json
import urllib.request
import urllib.parse
import time

BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def make_request(method, params=None):
    """Выполнить запрос к Telegram API"""
    url = f"{API_URL}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

print("🔍 Детальная диагностика бота\n")

# 1. Проверяем webhook
print("1️⃣ Информация о webhook:")
webhook_info = make_request("getWebhookInfo")
if webhook_info.get("ok"):
    result = webhook_info.get("result", {})
    print(f"   URL: {result.get('url', 'Не установлен')}")
    print(f"   Необработанных сообщений: {result.get('pending_update_count', 0)}")
    print(f"   Максимум соединений: {result.get('max_connections', 'не указано')}")
    print(f"   Разрешенные обновления: {result.get('allowed_updates', [])}")
    
    if result.get("last_error_message"):
        print(f"\n   ❌ Последняя ошибка: {result.get('last_error_message')}")
        print(f"   Время ошибки: {time.ctime(result.get('last_error_date', 0))}")
    
    if result.get("last_synchronization_error_date"):
        print(f"\n   ❌ Ошибка синхронизации: {time.ctime(result.get('last_synchronization_error_date'))}")

# 2. Проверяем доступность webhook URL
print("\n2️⃣ Проверяем доступность webhook URL:")
webhook_url = result.get('url', '')
if webhook_url:
    try:
        # Проверяем только заголовки
        req = urllib.request.Request(webhook_url, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"   ✅ URL доступен: {response.status} {response.reason}")
            print(f"   Сервер: {response.headers.get('Server', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ URL недоступен: {e}")

# 3. Пробуем отправить тестовый webhook
print("\n3️⃣ Тестируем webhook вручную:")
test_update = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "date": int(time.time()),
        "chat": {"id": 1, "type": "private"},
        "text": "/test",
        "from": {"id": 1, "is_bot": False, "first_name": "Test"}
    }
}

if webhook_url:
    try:
        data = json.dumps(test_update).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            print(f"   Статус: {response.status}")
            print(f"   Ответ: {response_data[:200]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

# 4. Получаем последние обновления
print("\n4️⃣ Последние обновления (polling):")
# Временно удаляем webhook для проверки
make_request("deleteWebhook")
time.sleep(1)

updates = make_request("getUpdates", {"limit": 5})
if updates.get("ok"):
    update_list = updates.get("result", [])
    if update_list:
        print(f"   Найдено {len(update_list)} обновлений:")
        for update in update_list:
            msg = update.get("message", {})
            if msg:
                print(f"\n   От: @{msg.get('from', {}).get('username', 'Unknown')}")
                print(f"   Текст: {msg.get('text', '')}")
                print(f"   Время: {time.ctime(msg.get('date', 0))}")
    else:
        print("   Нет новых сообщений")

# 5. Восстанавливаем webhook
print("\n5️⃣ Восстанавливаем webhook...")
if webhook_url:
    result = make_request("setWebhook", {"url": webhook_url})
    if result.get("ok"):
        print("   ✅ Webhook восстановлен")
    else:
        print(f"   ❌ Ошибка: {result}")

# 6. Проверяем health endpoint
print("\n6️⃣ Проверяем health endpoint:")
health_url = webhook_url.replace('/webhook', '/health')
try:
    with urllib.request.urlopen(health_url, timeout=5) as response:
        health_data = json.loads(response.read().decode('utf-8'))
        print(f"   Статус: {health_data.get('status', 'Unknown')}")
        checks = health_data.get('checks', {})
        if checks:
            print(f"   Database: {checks.get('database', {}).get('message', 'Unknown')}")
            print(f"   Config: {checks.get('config', {}).get('message', 'Unknown')}")
except Exception as e:
    print(f"   ❌ Health endpoint недоступен: {e}")

print("\n🔎 Рекомендации:")
print("1. Проверьте логи на Render.com Dashboard")
print("2. Убедитесь, что переменная WEBHOOK_URL содержит '-fkp8'")
print("3. Проверьте, что порт 10000 настроен правильно")
print("4. Возможно, требуется ручной redeploy на Render")