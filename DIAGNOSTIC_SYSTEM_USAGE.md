# 🎯 Ultimate Diagnostic System v2.0 - Руководство по Использованию

## 🚀 Быстрый Старт

### Полная Диагностика Проблемы
```bash
python3 ultimate_diagnostic_cli.py diagnose "Telegram бот не отвечает" \
  --error "webhook timeout after 30 seconds" \
  --full-analysis \
  --why-answers "Webhook таймаут,SSL медленный,Новый сертификат,Неподдерживаемый cipher suite,Неправильная конфигурация сервера"
```

### Быстрая Проверка Здоровья
```bash
python3 ultimate_diagnostic_cli.py quick-check
```

### Безопасная Реализация Решения
```bash
python3 ultimate_diagnostic_cli.py implement-solution "Исправить SSL конфигурацию" \
  --solution-file examples/fix_timeout_solution.py \
  --verification-file examples/verify_timeout_fix.py \
  --backup-files /etc/nginx/ssl.conf,/etc/ssl/webhook.crt
```

### Мониторинг После Решения
```bash
python3 ultimate_diagnostic_cli.py monitor --duration 60
```

## 🎯 Интерактивная Демонстрация

### Полная Демонстрация
```bash
python3 ultimate_diagnostic_demo.py
```

### Автоматическая Демонстрация
```bash
python3 ultimate_diagnostic_demo.py --auto
```

## 🔧 Создание Собственных Решений

### 1. Создайте файл решения (solution.py):
```python
def implement():
    """Главная функция реализации решения"""
    print("🔧 Исправляем проблему...")
    # Ваш код исправления
    return "Решение успешно применено"

def rollback():
    """Функция отката (опционально)"""
    print("🔄 Откатываем изменения...")
    # Ваш код отката
```

### 2. Создайте файл верификации (verification.py):
```python
def verify():
    """Главная функция верификации решения"""
    print("🧪 Проверяем решение...")
    # Ваши проверки
    return True  # True если все работает
```

### 3. Запустите безопасную реализацию:
```bash
python3 ultimate_diagnostic_cli.py implement-solution "Описание решения" \
  --solution-file solution.py \
  --verification-file verification.py
```

## 📊 Программное Использование

### Быстрая Диагностика
```python
from src.diagnostics import quick_diagnostic_session

report = quick_diagnostic_session(
    "Проблема с базой данных",
    error_message="Connection timeout",
    solution_function=my_fix_function,
    verification_function=my_verify_function
)
```

### Полная 6-Фазная Диагностика
```python
from src.diagnostics import UltimateDiagnosticSystem

system = UltimateDiagnosticSystem()

# Фаза 1: Триаж
triage = system.phase_1_triage("Описание проблемы", "Сообщение об ошибке")

# Фаза 2: Системная диагностика  
diagnosis = system.phase_2_systematic_diagnosis()

# Фаза 3: Тестирование гипотез
hypotheses = system.phase_3_hypothesis_testing()

# Фаза 4: Анализ корневой причины (5 Whys)
root_cause = system.phase_4_root_cause_analysis([
    "Причина 1", "Причина 2", "Причина 3", "Причина 4", "Корневая причина"
])

# Фаза 5: Безопасная реализация
implementation = system.phase_5_safe_solution_implementation(
    solution_description="Описание решения",
    implementation_function=my_solution,
    verification_function=my_verification
)

# Фаза 6: Мониторинг
monitoring = system.phase_6_post_solution_monitoring(monitoring_duration_minutes=30)

# Получить полный отчет
report = system.generate_comprehensive_report()
```

### Инструментация Функций
```python
from src.diagnostics import diagnose_function, DiagnosticLogger

logger = DiagnosticLogger("my_service")

@diagnose_function(logger)
def critical_function(data):
    """Функция с автоматической диагностикой"""
    # Автоматически логируются:
    # - Время выполнения
    # - Входные параметры  
    # - Результат выполнения
    # - Ошибки и исключения
    # - Системное состояние при ошибках
    return process_data(data)
```

## 🔥 ЖЕЛЕЗНЫЙ ЗАКОН

**НИКОГДА НЕ ПРЕДЛАГАЙ РЕШЕНИЕ БЕЗ ЗАВЕРШЕННОЙ ДИАГНОСТИКИ**

Система автоматически обеспечивает соблюдение этого правила:
- ✅ Обязательная фаза триажа
- ✅ Систематический анализ системы
- ✅ Научная валидация гипотез  
- ✅ Подтверждение корневой причины
- ✅ Безопасная реализация с откатом
- ✅ Мониторинг эффективности решения

## 📋 Полезные Команды

```bash
# Показать информацию о версии
python3 ultimate_diagnostic_cli.py version

# Показать отчет диагностики
python3 ultimate_diagnostic_cli.py show-report diagnostic_report_123456.json

# Помощь по CLI
python3 ultimate_diagnostic_cli.py --help
python3 ultimate_diagnostic_cli.py diagnose --help
python3 ultimate_diagnostic_cli.py implement-solution --help
```

## 🎯 Примеры Реальных Сценариев

### Telegram Бот Не Отвечает
```bash
python3 ultimate_diagnostic_cli.py diagnose "Telegram бот не отвечает на команды" \
  --error "webhook timeout after 30 seconds" \
  --context '{"environment":"production","recent_changes":"SSL certificate update"}'
```

### Медленные Запросы к БД
```bash
python3 ultimate_diagnostic_cli.py diagnose "Медленные запросы к базе данных" \
  --error "Query timeout after 10 seconds" \
  --hypotheses database_connectivity_issues,resource_exhaustion
```

### Проблемы с Google Calendar API
```bash
python3 ultimate_diagnostic_cli.py diagnose "Google Calendar API недоступен" \
  --error "403 Forbidden" \
  --hypotheses external_service_failure
```

Для получения дополнительной информации смотрите `PROJECT_SPECIFICATION.md`.