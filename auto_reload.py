#!/usr/bin/env python3
"""
Автоматический перезапуск бота при изменении файлов
"""
import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BotRestartHandler(FileSystemEventHandler):
    """Обработчик изменений файлов"""
    
    def __init__(self):
        self.bot_process = None
        self.last_restart = 0
        self.restart_delay = 2  # секунд между перезапусками
        
    def start_bot(self):
        """Запуск бота"""
        if self.bot_process:
            self.stop_bot()
            
        print("🚀 Запуск бота...")
        self.bot_process = subprocess.Popen(
            [sys.executable, "run_local.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
    def stop_bot(self):
        """Остановка бота"""
        if self.bot_process:
            print("🛑 Остановка бота...")
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("⚠️ Принудительная остановка...")
                self.bot_process.kill()
            self.bot_process = None
            
    def restart_bot(self):
        """Перезапуск бота с защитой от частых перезапусков"""
        current_time = time.time()
        if current_time - self.last_restart < self.restart_delay:
            return
            
        self.last_restart = current_time
        print("🔄 Перезапуск бота...")
        self.start_bot()
        
    def on_modified(self, event):
        """Обработка изменения файла"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Игнорируем некоторые файлы
        ignore_patterns = [
            '*.log', '*.db', '*.pyc', '*__pycache__*', 
            '*.git*', '*.env*', 'bot.log'
        ]
        
        for pattern in ignore_patterns:
            if file_path.match(pattern):
                return
                
        # Перезапускаем только для Python файлов в src/
        if (file_path.suffix == '.py' and 
            ('src' in file_path.parts or file_path.name.startswith('run_'))):
            print(f"📝 Изменен файл: {file_path}")
            self.restart_bot()

def main():
    """Главная функция автоперезагрузки"""
    print("🔄 Автоматический перезапуск бота при изменениях")
    print("=" * 50)
    
    handler = BotRestartHandler()
    observer = Observer()
    
    # Мониторим текущую директорию и src/
    paths_to_watch = ['.', 'src']
    for path in paths_to_watch:
        if Path(path).exists():
            observer.schedule(handler, path, recursive=True)
            print(f"👁️ Мониторинг: {path}")
    
    # Запускаем бота
    handler.start_bot()
    
    # Запускаем мониторинг
    observer.start()
    print("✅ Автоперезагрузка активна (Ctrl+C для остановки)")
    
    try:
        while True:
            time.sleep(1)
            # Проверяем, что бот еще работает
            if handler.bot_process and handler.bot_process.poll() is not None:
                print("⚠️ Бот остановился, перезапускаем...")
                handler.start_bot()
                
    except KeyboardInterrupt:
        print("\n🛑 Остановка автоперезагрузки...")
        observer.stop()
        handler.stop_bot()
        
    observer.join()
    print("✅ Автоперезагрузка остановлена")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("❌ Требуется библиотека watchdog:")
        print("pip install watchdog")
        sys.exit(1)