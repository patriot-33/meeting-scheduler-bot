#!/usr/bin/env python3
"""
🎯 БЫСТРАЯ ДИАГНОСТИКА MEETING-SCHEDULER-BOT
Упрощенная версия диагностической системы для быстрого запуска
"""

import sys
import os
import time
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def quick_system_check():
    """Быстрая проверка системы"""
    print("🎯 БЫСТРАЯ ДИАГНОСТИКА СИСТЕМЫ")
    print("=" * 50)
    
    # Импортируем базовые компоненты диагностики
    try:
        from diagnostics.core_diagnostics import DiagnosticLogger, log_system_state
        from diagnostics.system_monitor import SystemMonitor
        
        # Инициализируем логгер
        logger = DiagnosticLogger("quick_diagnostic", "quick_diagnostic.log")
        
        print("\n📊 СИСТЕМНЫЕ МЕТРИКИ:")
        print("-" * 25)
        
        # Логируем состояние системы
        log_system_state("QUICK_DIAGNOSTIC_START")
        
        # Создаем системный монитор
        monitor = SystemMonitor(logger)
        
        # Получаем текущие метрики
        metrics = monitor.get_current_metrics()
        
        print(f"CPU: {metrics.cpu_percent}%")
        print(f"Memory: {metrics.memory_percent}% ({metrics.memory_used_gb}GB/{metrics.memory_total_gb}GB)")
        print(f"Disk: {metrics.disk_percent}% ({metrics.disk_free_gb}GB свободно)")
        print(f"Сетевые соединения: {metrics.network_connections}")
        print(f"Процессы: {metrics.process_count}")
        
        # Анализ трендов
        print(f"\n📈 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:")
        print("-" * 30)
        
        # Добавим несколько метрик для анализа тренда
        for i in range(3):
            time.sleep(1)
            metrics = monitor.get_current_metrics()
        
        trends = monitor.analyze_performance_trends(minutes=1)
        
        print(f"CPU - текущий: {trends['cpu']['current']:.1f}%, средний: {trends['cpu']['average']:.1f}%")
        print(f"Memory - текущий: {trends['memory']['current']:.1f}%, средний: {trends['memory']['average']:.1f}%")
        
        if trends.get('alerts'):
            print(f"\n🚨 ПРЕДУПРЕЖДЕНИЯ:")
            for alert in trends['alerts']:
                print(f"   {alert}")
        else:
            print(f"\n✅ Система работает в нормальном режиме")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при диагностике: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Тест подключения к базе данных"""
    print(f"\n🗄️  ТЕСТ БАЗЫ ДАННЫХ:")
    print("-" * 22)
    
    try:
        # Попробуем импортировать database модуль
        import database
        
        # Проверим, есть ли engine
        if hasattr(database, 'engine'):
            engine = database.engine
            print("✅ Database engine найден")
            
            # Попробуем выполнить простой запрос
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            print("✅ Подключение к базе данных успешно")
            
            # Проверим pool info если доступно
            if hasattr(engine, 'pool'):
                pool = engine.pool
                print(f"   Connection pool size: {pool.size()}")
                print(f"   Checked out connections: {pool.checkedout()}")
            
            return True
            
        else:
            print("⚠️  Database engine не найден в модуле database")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def test_external_services():
    """Тест внешних сервисов"""
    print(f"\n🌐 ТЕСТ ВНЕШНИХ СЕРВИСОВ:")
    print("-" * 27)
    
    try:
        import requests
        
        services = {
            "Google APIs": "https://www.googleapis.com/",
            "Google OAuth": "https://oauth2.googleapis.com/", 
            "Telegram Bot API": "https://api.telegram.org/"
        }
        
        for service_name, url in services.items():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code < 500:
                    print(f"✅ {service_name}: {response.status_code} ({response_time:.0f}ms)")
                else:
                    print(f"⚠️  {service_name}: {response.status_code} ({response_time:.0f}ms)")
                    
            except Exception as e:
                print(f"❌ {service_name}: {e}")
        
        return True
        
    except ImportError:
        print("❌ requests модуль не найден")
        return False

def test_project_structure():
    """Проверка структуры проекта"""
    print(f"\n📁 СТРУКТУРА ПРОЕКТА:")
    print("-" * 21)
    
    critical_files = [
        "src/main.py",
        "src/config.py", 
        "src/database.py",
        "src/handlers/",
        "src/services/",
        "src/utils/",
        "requirements.txt"
    ]
    
    all_good = True
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - НЕ НАЙДЕН")
            all_good = False
    
    # Проверим наши диагностические файлы
    diagnostic_files = [
        "src/diagnostics/",
        "src/diagnostics/core_diagnostics.py",
        "src/diagnostics/system_monitor.py"
    ]
    
    print(f"\n🔧 ДИАГНОСТИЧЕСКИЕ КОМПОНЕНТЫ:")
    for file_path in diagnostic_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - НЕ НАЙДЕН") 
            all_good = False
    
    return all_good

def run_hypothesis_tests():
    """Запуск базовых тестов гипотез"""
    print(f"\n🧪 ТЕСТИРОВАНИЕ ГИПОТЕЗ:")
    print("-" * 23)
    
    try:
        from diagnostics.hypothesis_testing import HypothesisTester, CommonHypotheses
        from diagnostics.core_diagnostics import DiagnosticLogger
        
        logger = DiagnosticLogger("hypothesis_test")
        tester = HypothesisTester(logger)
        
        # Тест гипотезы истощения ресурсов
        print("Тестирую гипотезу: Истощение системных ресурсов...")
        conditions = CommonHypotheses.create_resource_exhaustion_hypothesis()
        result = tester.test_hypothesis(
            "Resource Exhaustion Test",
            conditions,
            required_success_rate=1.0
        )
        
        print(f"Результат: {result.overall_result.value}")
        print(f"Прошло тестов: {result.conditions_passed}/{result.conditions_tested}")
        print(f"Заключение: {result.conclusion}")
        
        if result.recommendations:
            print("Рекомендации:")
            for rec in result.recommendations:
                print(f"   • {rec}")
        
        return result.overall_result.value == "CONFIRMED"
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании гипотез: {e}")
        return False

def main():
    """Основная функция быстрой диагностики"""
    
    start_time = time.time()
    results = {}
    
    print("🚀 ЗАПУСК БЫСТРОЙ ДИАГНОСТИКИ")
    print("=" * 50)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Проверка структуры проекта
    results['project_structure'] = test_project_structure()
    
    # 2. Системные метрики
    results['system_check'] = quick_system_check()
    
    # 3. База данных
    results['database'] = test_database_connection()
    
    # 4. Внешние сервисы
    results['external_services'] = test_external_services()
    
    # 5. Тестирование гипотез
    results['hypothesis_tests'] = run_hypothesis_tests()
    
    # Итоговый отчет
    duration = time.time() - start_time
    
    print(f"\n📋 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 20)
    print(f"Время выполнения: {duration:.1f} секунд")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    print(f"Тестов пройдено: {passed_tests}/{total_tests}")
    
    for test_name, result in results.items():
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Система готова к работе")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n⚠️  СИСТЕМА В РАБОЧЕМ СОСТОЯНИИ")
        print(f"Некоторые компоненты требуют внимания")
    else:
        print(f"\n🚨 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("Требуется детальная диагностика")
    
    print(f"\n📄 Подробные логи сохранены в:")
    print("   • quick_diagnostic.log")
    
    return passed_tests / total_tests

if __name__ == "__main__":
    try:
        success_rate = main()
        exit(0 if success_rate >= 0.8 else 1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Диагностика прервана пользователем")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()
        exit(1)