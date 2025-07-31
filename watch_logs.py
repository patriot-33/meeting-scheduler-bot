#!/usr/bin/env python3
"""
Мониторинг логов в реальном времени с фильтрацией и раскраской
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# ANSI цвета для терминала
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize_log_line(line):
    """Раскрашивает строку лога в зависимости от уровня"""
    line = line.strip()
    
    if not line:
        return line
    
    # Ошибки - красным
    if "ERROR" in line or "❌" in line or "FAILED" in line:
        return f"{Colors.RED}{line}{Colors.END}"
    
    # Предупреждения - желтым
    elif "WARNING" in line or "⚠️" in line:
        return f"{Colors.YELLOW}{line}{Colors.END}"
    
    # Успех - зеленым
    elif "✅" in line or "SUCCESS" in line:
        return f"{Colors.GREEN}{line}{Colors.END}"
    
    # Важная информация - синим
    elif "🚀" in line or "🔧" in line or "📥" in line:
        return f"{Colors.BLUE}{line}{Colors.END}"
    
    # Диагностика - фиолетовым
    elif "🔍" in line or "DEBUG" in line:
        return f"{Colors.MAGENTA}{line}{Colors.END}"
    
    # Обычный текст
    else:
        return line

def watch_bot_logs():
    """Мониторинг логов бота"""
    print(f"{Colors.BOLD}🔍 Мониторинг логов Meeting Scheduler Bot{Colors.END}")
    print(f"{Colors.CYAN}Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print("=" * 60)
    
    log_file = Path("bot.log")
    
    # Создаем файл лога если не существует
    if not log_file.exists():
        log_file.touch()
        print(f"{Colors.YELLOW}📄 Создан файл лога: {log_file}{Colors.END}")
    
    # Показываем последние 20 строк
    try:
        result = subprocess.run(['tail', '-n', '20', str(log_file)], 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"{Colors.CYAN}--- Последние записи ---{Colors.END}")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(colorize_log_line(line))
            print(f"{Colors.CYAN}--- Мониторинг в реальном времени ---{Colors.END}")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Не удалось показать историю: {e}{Colors.END}")
    
    # Мониторинг в реальном времени
    try:
        process = subprocess.Popen(['tail', '-f', str(log_file)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        
        print(f"{Colors.GREEN}👁️ Мониторинг запущен (Ctrl+C для остановки){Colors.END}")
        
        for line in iter(process.stdout.readline, ''):
            if line:
                print(colorize_log_line(line.rstrip()))
                
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Мониторинг остановлен{Colors.END}")
        if process:
            process.terminate()
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка мониторинга: {e}{Colors.END}")

def watch_filters():
    """Мониторинг с фильтрами"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Мониторинг логов с фильтрами")
    parser.add_argument("--errors", action="store_true", help="Только ошибки")
    parser.add_argument("--webhook", action="store_true", help="Только webhook события")
    parser.add_argument("--meetings", action="store_true", help="Только события создания встреч")
    parser.add_argument("--oauth", action="store_true", help="Только OAuth события")
    
    args = parser.parse_args()
    
    log_file = Path("bot.log")
    
    if not log_file.exists():
        print(f"{Colors.RED}❌ Файл лога не найден: {log_file}{Colors.END}")
        return
    
    # Настройка фильтра
    filter_patterns = []
    if args.errors:
        filter_patterns.extend(["ERROR", "❌", "FAILED"])
    if args.webhook:
        filter_patterns.extend(["WEBHOOK", "📥"])
    if args.meetings:
        filter_patterns.extend(["MEETING", "🤝", "BOOKING"])
    if args.oauth:
        filter_patterns.extend(["OAUTH", "🔐", "CALENDAR"])
    
    try:
        process = subprocess.Popen(['tail', '-f', str(log_file)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        
        filter_desc = f" (фильтр: {', '.join(filter_patterns)})" if filter_patterns else ""
        print(f"{Colors.GREEN}👁️ Мониторинг запущен{filter_desc}{Colors.END}")
        
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                if not filter_patterns or any(pattern in line for pattern in filter_patterns):
                    print(colorize_log_line(line))
                    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Мониторинг остановлен{Colors.END}")
        if process:
            process.terminate()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        watch_filters()
    else:
        watch_bot_logs()