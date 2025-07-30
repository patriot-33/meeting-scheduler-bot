#!/usr/bin/env python3
"""
Проверка статуса сервиса на Render
"""
import urllib.request
import json
import time

print("🔍 Проверка сервиса на Render\n")

# Базовый URL сервиса
base_url = "https://meeting-scheduler-bot-fkp8.onrender.com"

# Список endpoints для проверки
endpoints = [
    ("", "Главная страница"),
    ("/health", "Health check"),
    ("/webhook", "Webhook endpoint"),
]

for endpoint, description in endpoints:
    url = base_url + endpoint
    print(f"📍 Проверяем {description}: {url}")
    
    try:
        start_time = time.time()
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            elapsed = time.time() - start_time
            content = response.read().decode('utf-8')
            
            print(f"   ✅ Статус: {response.status}")
            print(f"   Время ответа: {elapsed:.2f}s")
            print(f"   Размер: {len(content)} байт")
            
            # Показываем первые 200 символов ответа
            if content:
                preview = content[:200].replace('\n', ' ')
                print(f"   Содержимое: {preview}...")
                
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP ошибка: {e.code} {e.reason}")
        
    except urllib.error.URLError as e:
        print(f"   ❌ Ошибка подключения: {e.reason}")
        
    except Exception as e:
        print(f"   ❌ Неизвестная ошибка: {e}")
    
    print()

print("\n📊 Альтернативная проверка (без -fkp8):")
alt_url = "https://meeting-scheduler-bot.onrender.com"
try:
    req = urllib.request.Request(alt_url)
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"   ✅ {alt_url} - Статус: {response.status}")
except Exception as e:
    print(f"   ❌ {alt_url} - Ошибка: {e}")

print("\n💡 Выводы:")
print("- Если все endpoints недоступны - сервис не запущен или крашится")
print("- Проверьте статус на https://dashboard.render.com")
print("- Возможно, нужен manual deploy или restart")