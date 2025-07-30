#!/bin/bash

# Скрипт для загрузки кода на GitHub

echo "🚀 Начинаем загрузку на GitHub..."

# Инициализация Git
git init

# Добавление всех файлов
git add .

# Создание коммита
git commit -m "Fix syntax errors and encoding issues in manager.py and reminder_service.py"

# Добавление удаленного репозитория
git remote add origin https://github.com/patriot-33/meeting-scheduler-bot.git

# Переключение на ветку main
git branch -M main

# Загрузка на GitHub
git push -u origin main

echo "✅ Код успешно загружен на GitHub!"