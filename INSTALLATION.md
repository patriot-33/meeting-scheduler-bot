# 🚀 Инструкция по Установке - Meeting Scheduler Bot

## 📋 Быстрая Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/patriot-33/meeting-scheduler-bot.git
cd meeting-scheduler-bot
```

### 2. Установка зависимостей
```bash
# Обновление pip
pip install --upgrade pip

# Установка всех зависимостей
pip install -r requirements.txt
```

### 3. Настройка окружения
```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

### 4. Проверка установки диагностической системы
```bash
# Быстрая проверка
python3 ultimate_diagnostic_cli.py version

# Проверка здоровья системы
python3 ultimate_diagnostic_cli.py quick-check

# Демонстрация возможностей
python3 ultimate_diagnostic_demo.py --auto
```

## 🔧 Устранение Проблем

### ❌ ModuleNotFoundError: No module named 'schedule'
```bash
pip install schedule==1.2.0
```

### ❌ ModuleNotFoundError: No module named 'click'
```bash
pip install click==8.1.7
```

### ❌ ModuleNotFoundError: No module named 'requests'
```bash
pip install requests==2.31.0
```

### ❌ SQLAlchemy compatibility issues
Убедитесь, что используется SQLAlchemy 2.0+:
```bash
pip install --upgrade SQLAlchemy==2.0.23
```

### ❌ Полная переустановка зависимостей
```bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## 🐍 Поддерживаемые версии Python

- ✅ **Python 3.9+** (рекомендуется)
- ✅ **Python 3.10**
- ✅ **Python 3.11**
- ⚠️ **Python 3.8** (минимальная поддержка)

### Проверка версии Python
```bash
python3 --version
```

## 🗄️ Настройка Базы Данных

### SQLite (для разработки)
```bash
# База данных создается автоматически
python3 -c "from src.database import get_database_engine; get_database_engine()"
```

### PostgreSQL (для production)
```bash
# Установка в .env
DATABASE_URL=postgresql://user:password@localhost/dbname

# Проверка подключения
python3 -c "from src.database import get_database_engine; print('DB OK') if get_database_engine() else print('DB FAIL')"
```

## 🎯 Проверка Диагностической Системы

### Полная диагностика системы
```bash
python3 ultimate_diagnostic_cli.py diagnose "Тестовая проблема" --error "test error" --full-analysis
```

### Тест всех компонентов
```bash
# Проверка системного мониторинга
python3 -c "from src.diagnostics.system_monitor import SystemMonitor; from src.diagnostics.core_diagnostics import diagnostic_logger; print('✅ System Monitor OK') if SystemMonitor(diagnostic_logger).get_current_metrics() else print('❌ System Monitor FAIL')"

# Проверка тестирования гипотез
python3 -c "from src.diagnostics.hypothesis_testing import HypothesisTester; from src.diagnostics.core_diagnostics import diagnostic_logger; print('✅ Hypothesis Testing OK')"

# Проверка безопасной реализации
python3 -c "from src.diagnostics.safe_implementation import SafeImplementationManager; from src.diagnostics.core_diagnostics import diagnostic_logger; print('✅ Safe Implementation OK')"

# Проверка мониторинга
python3 -c "from src.diagnostics.post_solution_monitoring import PostSolutionMonitor; from src.diagnostics.core_diagnostics import diagnostic_logger; print('✅ Post Solution Monitoring OK')"
```

## 🔍 Диагностика Проблем

### Если диагностическая система не запускается:

1. **Проверьте все зависимости:**
```bash
python3 -c "
import sys
modules = ['schedule', 'click', 'requests', 'psutil', 'sqlalchemy']
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        print(f'❌ {module} - run: pip install {module}')
"
```

2. **Проверьте права доступа:**
```bash
ls -la ultimate_diagnostic_cli.py
chmod +x ultimate_diagnostic_cli.py
```

3. **Проверьте PYTHONPATH:**
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
python3 ultimate_diagnostic_cli.py version
```

### Если есть проблемы с импортами:

1. **Добавьте src в PYTHONPATH:**
```bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
```

2. **Или используйте полный путь:**
```bash
python3 -m src.diagnostics.diagnostic_orchestrator
```

## 🌐 Codespaces / GitHub Environments

### Для GitHub Codespaces:
```bash
# В терминале Codespaces
cd /workspaces/meeting-scheduler-bot

# Установка зависимостей
pip install -r requirements.txt

# Проверка
python3 ultimate_diagnostic_cli.py version
```

### Для Replit:
```bash
# В Shell Replit
pip install -r requirements.txt
python3 ultimate_diagnostic_cli.py quick-check
```

### Для локальной разработки:
```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

## ✅ Проверка Успешной Установки

После установки все эти команды должны работать без ошибок:

```bash
# 1. Версия системы
python3 ultimate_diagnostic_cli.py version

# 2. Быстрая диагностика
python3 ultimate_diagnostic_cli.py quick-check

# 3. Демо системы
python3 ultimate_diagnostic_demo.py --telegram

# 4. Проверка примеров
python3 -c "from examples.fix_timeout_solution import implement; print('✅ Examples OK')"
```

## 🆘 Получение Помощи

Если проблемы не устраняются:

1. **Создайте issue на GitHub:**
   https://github.com/patriot-33/meeting-scheduler-bot/issues

2. **Запустите полную диагностику:**
```bash
python3 ultimate_diagnostic_cli.py diagnose "Installation problem" --error "Cannot run CLI" > installation_debug.log 2>&1
```

3. **Приложите к issue:**
   - Версию Python: `python3 --version`
   - Операционную систему
   - Файл `installation_debug.log`
   - Вывод `pip list`

---

**🎯 После успешной установки система диагностики готова к использованию!**