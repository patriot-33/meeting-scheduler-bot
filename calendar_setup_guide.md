# 📅 ПОДРОБНАЯ ИНСТРУКЦИЯ: НАСТРОЙКА ДОСТУПА К GOOGLE CALENDAR

## 🎯 **ЦЕЛЬ**: Дать Service Account доступ к календарю

**Service Account Email**: `meeting-bot-service@meeting-scheduler-bot-467415.iam.gserviceaccount.com`

---

## 📋 **ПОШАГОВАЯ ИНСТРУКЦИЯ**

### **Шаг 1: Открыть Google Calendar**
1. Перейти на: https://calendar.google.com/
2. **ВАЖНО**: Войти под аккаунтом **plantatorbob@gmail.com** (владелец календаря)

### **Шаг 2: Найти нужный календарь**
В левой панели найти один из вариантов:
- **"plantatorbob@gmail.com"**
- **"Основной"** (или "Primary")
- **Календарь с вашим именем/email**

### **Шаг 3: Открыть настройки календаря**
1. **Навести курсор** на название календаря
2. Должны появиться **три точки (⋮)** справа
3. **Кликнуть на три точки**
4. Выбрать **"Settings and sharing"** (Настройки и общий доступ)

### **Шаг 4: Настроить общий доступ**
1. Прокрутить страницу вниз до раздела **"Share with specific people or groups"**
2. Нажать кнопку **"+ Add people and groups"**

### **Шаг 5: Добавить Service Account**
1. В поле **"Add email or name"** ввести:
   ```
   meeting-bot-service@meeting-scheduler-bot-467415.iam.gserviceaccount.com
   ```

2. В выпадающем списке **"Permissions"** выбрать:
   - **"Make changes to events"** (рекомендуется)
   - ИЛИ **"Make changes and manage sharing"** (если нужны расширенные права)

3. Нажать **"Send"**

### **Шаг 6: Подтверждение**
- Может появиться предупреждение о том, что email не найден - это нормально для Service Account
- Нажать **"Send anyway"** или **"OK"**

---

## 🔍 **КАК ПРОВЕРИТЬ ЧТО ВСЕ ПРАВИЛЬНО**

После настройки в разделе **"Share with specific people"** должна появиться строка:
```
meeting-bot-service@meeting-scheduler-bot-467415.iam.gserviceaccount.com
Permission: Make changes to events
```

---

## ⚠️ **ЧАСТЫЕ ОШИБКИ**

### **Ошибка 1: Неправильный календарь**
- Убедитесь что настраиваете основной календарь, а не дополнительный
- В .env файле указан `GOOGLE_CALENDAR_ID_1=plantatorbob@gmail.com`

### **Ошибка 2: Неправильный email**
- Точный email: `meeting-bot-service@meeting-scheduler-bot-467415.iam.gserviceaccount.com`
- Проверьте каждый символ!

### **Ошибка 3: Недостаточные права**
- Минимум: "See all event details" - НЕ РАБОТАЕТ для создания
- Нужно: "Make changes to events" - РАБОТАЕТ
- Лучше: "Make changes and manage sharing" - РАБОТАЕТ с запасом

### **Ошибка 4: Неправильный аккаунт Google**
- Должны быть залогинены как **plantatorbob@gmail.com**
- Если используете несколько аккаунтов Google, проверьте какой активен

---

## 🧪 **ТЕСТИРОВАНИЕ**

После настройки подождите 1-2 минуты и запустите:

```bash
# Тест с ожиданием синхронизации
python3 wait_and_test.py

# Или прямой тест
python3 test_calendar_access.py
```

---

## 🆘 **ЕСЛИ НЕ РАБОТАЕТ**

### **Вариант А: Проверить текущие настройки**
1. Открыть настройки календаря
2. Посмотреть раздел "Share with specific people"
3. Убедиться что Service Account там есть

### **Вариант Б: Удалить и добавить заново**
1. Найти Service Account в списке общего доступа
2. Нажать X (удалить)
3. Добавить заново с правильными правами

### **Вариант В: Использовать другой календарь**
Если основной календарь не работает, можно создать новый:
1. В левой панели нажать "+" рядом с "Other calendars"
2. "Create new calendar"
3. Дать название, например "Meeting Bot Calendar"
4. Скопировать ID нового календаря
5. Обновить в .env: `GOOGLE_CALENDAR_ID_1=новый_calendar_id`

---

## 📞 **ПОДДЕРЖКА**

Если проблемы остаются, предоставьте:
1. Скриншот настроек календаря (раздел "Share with specific people")
2. Результат выполнения `python3 test_calendar_access.py`
3. Какой аккаунт Google используете для настройки