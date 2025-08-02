#!/usr/bin/env python3
"""
🛡️ HOLISTIC PYTHON BACKEND DIAGNOSTIC & REPAIR SYSTEM v4.0
Senior Python Backend архитектор с 15+ лет опыта
АНТИХРУПКАЯ система диагностики с ОБЯЗАТЕЛЬНЫМ сохранением ВСЕЙ истории
"""

import json
import sqlite3
import pickle
import hashlib
import shutil
import asyncio
import traceback
import multiprocessing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import sys

# Core principles
DIAGNOSTIC_RULES = {
    "NEVER_ASSUME": "Проверяй каждое предположение",
    "THINK_GLOBALLY": "Любое изменение влияет на ВСЮ систему",
    "INCREMENTAL_FIXES": "Маленькие шаги с проверкой после каждого",
    "PRESERVE_INVARIANTS": "Не нарушай существующие контракты",
    "TEST_EVERYTHING": "Непроверенное изменение = новый баг",
    "DOCUMENT_EVERYTHING": "Каждое изменение ДОЛЖНО быть задокументировано",
    "NEVER_LOSE_HISTORY": "История изменений - священна, НИКОГДА не теряй данные"
}

class MandatoryHistoryPersistence:
    """КРИТИЧЕСКИ ВАЖНО: Система обязательного сохранения ВСЕЙ истории"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history_root = self.project_root / ".diagnostic_history"
        self.history_root.mkdir(exist_ok=True)
        
        # Множественные системы хранения для надежности
        self.db_path = self.history_root / "diagnostic_history.db"
        self.json_backup = self.history_root / "history_backup.json"
        self.pickle_backup = self.history_root / "history_backup.pkl"
        
        # Инициализация БД
        self._init_database()
        
        # Инициализация лог-файла
        self.log_file = self.history_root / "diagnostic.log"
        
    def _init_database(self):
        """Инициализация SQLite БД для истории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица сессий диагностики
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostic_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                problem_description TEXT,
                final_status TEXT,
                full_data TEXT
            )
        """)
        
        # Таблица всех изменений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS changes (
                change_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                file_path TEXT,
                change_type TEXT,
                diff_content TEXT,
                metrics_before TEXT,
                metrics_after TEXT,
                rollback_info TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
            )
        """)
        
        # Таблица багов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bugs (
                bug_id TEXT PRIMARY KEY,
                session_id TEXT,
                discovery_time TIMESTAMP,
                bug_type TEXT,
                severity TEXT,
                root_cause TEXT,
                fix_applied TEXT,
                prevention_measures TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
            )
        """)
        
        # Таблица проблем
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                issue_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                description TEXT,
                severity TEXT,
                component TEXT,
                fix_status TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
    def _generate_id(self, prefix: str) -> str:
        """Генерация уникального ID"""
        timestamp = datetime.now().isoformat()
        hash_part = hashlib.md5(f"{timestamp}{prefix}".encode()).hexdigest()[:8]
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash_part}"
    
    def _log(self, message: str, level: str = "INFO"):
        """Логирование с обязательным сохранением"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"🔍 [{level}] {message}")
    
    def save_session_start(self, session_data: Dict[str, Any]):
        """ОБЯЗАТЕЛЬНОЕ сохранение начала сессии"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверить существование столбцов и добавить если нужно
        cursor.execute("PRAGMA table_info(diagnostic_sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'problem_description' not in columns:
            cursor.execute("ALTER TABLE diagnostic_sessions ADD COLUMN problem_description TEXT")
            conn.commit()
            
        if 'full_data' not in columns:
            cursor.execute("ALTER TABLE diagnostic_sessions ADD COLUMN full_data TEXT")
            conn.commit()
        
        cursor.execute("""
            INSERT INTO diagnostic_sessions (
                session_id, start_time, problem_description, full_data
            ) VALUES (?, ?, ?, ?)
        """, (
            session_data['session_id'],
            session_data['start_time'],
            session_data['problem_description'],
            json.dumps(session_data)
        ))
        
        conn.commit()
        conn.close()
        
        self._log(f"Session started: {session_data['session_id']}")
    
    def save_issue(self, issue_data: Dict[str, Any]) -> str:
        """ОБЯЗАТЕЛЬНОЕ сохранение проблемы"""
        issue_id = self._generate_id("issue")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO issues (
                issue_id, session_id, timestamp, description,
                severity, component, fix_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            issue_id,
            issue_data.get('session_id'),
            datetime.now().isoformat(),
            issue_data.get('description'),
            issue_data.get('severity', 'medium'),
            issue_data.get('component'),
            'discovered'
        ))
        
        conn.commit()
        conn.close()
        
        self._log(f"Issue saved: {issue_id} - {issue_data.get('description')}")
        return issue_id

class SystemAnalyzer:
    """Анализ системы с построением полной карты"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history = MandatoryHistoryPersistence(project_root)
        
    def analyze_complete_system(self) -> Dict[str, Any]:
        """Построить полную карту системы ПЕРЕД любыми изменениями"""
        self.history._log("Начинаю полный анализ системы")
        analysis_start = datetime.now()
        
        # 1. Найти все Python файлы
        python_files = list(self.project_root.rglob("*.py"))
        self.history._log(f"Найдено Python файлов: {len(python_files)}")
        
        # 2. Анализировать структуру проекта
        project_structure = self.analyze_project_structure()
        
        # 3. Найти критические файлы
        critical_files = self.identify_critical_files()
        
        # 4. Анализировать зависимости
        dependencies = self.analyze_dependencies()
        
        # 5. Найти потенциальные проблемные места
        problem_patterns = self.detect_problem_patterns()
        
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "total_python_files": len(python_files),
            "project_structure": project_structure,
            "critical_files": critical_files,
            "dependencies": dependencies,
            "problem_patterns": problem_patterns,
            "analysis_time": (datetime.now() - analysis_start).total_seconds()
        }
        
        # ОБЯЗАТЕЛЬНО сохранить результат анализа
        analysis_file = self.history.history_root / "system_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        self.history._log(f"Анализ системы завершен за {analysis_result['analysis_time']:.2f} сек")
        return analysis_result
    
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Анализ структуры проекта"""
        structure = {
            "src_directory": str(self.project_root / "src"),
            "has_database": (self.project_root / "src" / "database.py").exists(),
            "has_services": (self.project_root / "src" / "services").exists(),
            "has_handlers": (self.project_root / "src" / "handlers").exists(),
            "has_config": (self.project_root / "src" / "config.py").exists(),
            "has_tests": (self.project_root / "tests").exists(),
            "has_requirements": (self.project_root / "requirements.txt").exists(),
            "has_docker": (self.project_root / "Dockerfile").exists()
        }
        
        return structure
    
    def identify_critical_files(self) -> List[str]:
        """Определить критически важные файлы"""
        critical_patterns = [
            "database.py", "main.py", "config.py",
            "meeting_service.py", "google_calendar",
            "oauth_service.py"
        ]
        
        critical_files = []
        for pattern in critical_patterns:
            matches = list(self.project_root.rglob(f"*{pattern}*"))
            critical_files.extend([str(f) for f in matches])
        
        return critical_files
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Анализ зависимостей проекта"""
        dependencies = {
            "internal": [],
            "external": [],
            "database_related": [],
            "calendar_related": [],
            "telegram_related": []
        }
        
        # Анализ imports в файлах
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Найти импорты
                import_lines = [line.strip() for line in content.split('\n') 
                              if line.strip().startswith(('import ', 'from '))]
                
                for imp in import_lines:
                    if 'database' in imp.lower():
                        dependencies["database_related"].append(f"{py_file.name}: {imp}")
                    elif 'google' in imp.lower() or 'calendar' in imp.lower():
                        dependencies["calendar_related"].append(f"{py_file.name}: {imp}")
                    elif 'telegram' in imp.lower():
                        dependencies["telegram_related"].append(f"{py_file.name}: {imp}")
                        
            except Exception as e:
                self.history._log(f"Ошибка анализа {py_file}: {e}", "ERROR")
        
        return dependencies
    
    def detect_problem_patterns(self) -> List[Dict[str, Any]]:
        """Обнаружение паттернов проблем"""
        patterns = []
        
        # Найти файлы с дублированием логики
        calendar_files = list(self.project_root.rglob("*calendar*.py"))
        if len(calendar_files) > 1:
            patterns.append({
                "type": "potential_duplication",
                "description": f"Найдено {len(calendar_files)} файлов с calendar в имени",
                "files": [str(f) for f in calendar_files],
                "severity": "medium"
            })
        
        # Найти большие файлы
        for py_file in self.project_root.rglob("*.py"):
            try:
                line_count = sum(1 for _ in open(py_file, 'r', encoding='utf-8'))
                if line_count > 500:
                    patterns.append({
                        "type": "large_file",
                        "description": f"Большой файл: {line_count} строк",
                        "file": str(py_file),
                        "lines": line_count,
                        "severity": "low"
                    })
            except Exception:
                pass
        
        return patterns

class MeetingDuplicationAnalyzer:
    """Специализированный анализатор дублирования встреч"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history = MandatoryHistoryPersistence(project_root)
        
    def analyze_meeting_duplication(self) -> Dict[str, Any]:
        """Анализ проблемы дублирования встреч"""
        self.history._log("Начинаю анализ дублирования встреч")
        
        analysis = {
            "problems_detected": [],
            "root_causes": [],
            "affected_files": [],
            "fix_recommendations": []
        }
        
        # 1. Найти все файлы связанные с календарем
        calendar_files = self.find_calendar_related_files()
        analysis["affected_files"] = calendar_files
        
        # 2. Анализировать создание встреч
        creation_analysis = self.analyze_meeting_creation()
        analysis["creation_analysis"] = creation_analysis
        
        # 3. Анализировать удаление встреч
        deletion_analysis = self.analyze_meeting_deletion()
        analysis["deletion_analysis"] = deletion_analysis
        
        # 4. Найти корневые причины
        root_causes = self.identify_root_causes(creation_analysis, deletion_analysis)
        analysis["root_causes"] = root_causes
        
        # 5. Сгенерировать рекомендации
        recommendations = self.generate_fix_recommendations(root_causes)
        analysis["fix_recommendations"] = recommendations
        
        # ОБЯЗАТЕЛЬНО сохранить анализ
        analysis_file = self.history.history_root / "meeting_duplication_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return analysis
    
    def find_calendar_related_files(self) -> List[str]:
        """Найти все файлы связанные с календарем"""
        patterns = ["*calendar*", "*meeting*", "*event*", "*google*"]
        files = []
        
        for pattern in patterns:
            matches = list(self.project_root.rglob(f"{pattern}.py"))
            files.extend([str(f) for f in matches])
        
        return files
    
    def analyze_meeting_creation(self) -> Dict[str, Any]:
        """Анализ логики создания встреч"""
        self.history._log("Анализирую логику создания встреч")
        
        analysis = {
            "creation_methods": [],
            "potential_duplications": [],
            "calendar_services": []
        }
        
        # Найти все методы создания
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Поиск методов создания
                if 'create_meeting' in content:
                    analysis["creation_methods"].append({
                        "file": str(py_file),
                        "method": "create_meeting",
                        "line_count": content.count('create_meeting')
                    })
                
                if 'create_event' in content:
                    analysis["creation_methods"].append({
                        "file": str(py_file),
                        "method": "create_event", 
                        "line_count": content.count('create_event')
                    })
                
                # Поиск дублирования
                if content.count('events().insert') > 1:
                    analysis["potential_duplications"].append({
                        "file": str(py_file),
                        "description": f"Множественные вызовы events().insert: {content.count('events().insert')}"
                    })
                
            except Exception as e:
                self.history._log(f"Ошибка анализа {py_file}: {e}", "ERROR")
        
        return analysis
    
    def analyze_meeting_deletion(self) -> Dict[str, Any]:
        """Анализ логики удаления встреч"""
        self.history._log("Анализирую логику удаления встреч")
        
        analysis = {
            "deletion_methods": [],
            "potential_issues": []
        }
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Поиск методов удаления
                if 'cancel_meeting' in content or 'delete_meeting' in content:
                    analysis["deletion_methods"].append({
                        "file": str(py_file),
                        "has_cancel": 'cancel_meeting' in content,
                        "has_delete": 'delete_meeting' in content
                    })
                
                # Поиск проблем с удалением
                if 'events().delete' in content:
                    delete_count = content.count('events().delete')
                    if delete_count == 1:
                        analysis["potential_issues"].append({
                            "file": str(py_file),
                            "issue": "Только один вызов delete для потенциально множественных событий"
                        })
                
            except Exception as e:
                self.history._log(f"Ошибка анализа {py_file}: {e}", "ERROR")
        
        return analysis
    
    def identify_root_causes(self, creation_analysis: Dict, deletion_analysis: Dict) -> List[Dict[str, Any]]:
        """Определить корневые причины проблем"""
        root_causes = []
        
        # Анализ дублирования при создании
        creation_methods_count = len(creation_analysis["creation_methods"])
        if creation_methods_count > 1:
            root_causes.append({
                "type": "multiple_creation_paths",
                "description": f"Обнаружено {creation_methods_count} различных методов создания встреч",
                "severity": "high",
                "impact": "Может приводить к множественному созданию событий"
            })
        
        # Анализ проблем с удалением
        if deletion_analysis["potential_issues"]:
            root_causes.append({
                "type": "incomplete_deletion",
                "description": "Неполное удаление событий из множественных календарей",
                "severity": "high", 
                "impact": "События остаются в календарях после удаления в боте"
            })
        
        # Анализ дублирования событий
        for dup in creation_analysis["potential_duplications"]:
            root_causes.append({
                "type": "event_duplication_in_code",
                "description": f"Множественные вызовы events().insert в {dup['file']}",
                "severity": "critical",
                "impact": "Прямое дублирование событий в календаре"
            })
        
        return root_causes
    
    def generate_fix_recommendations(self, root_causes: List[Dict]) -> List[Dict[str, Any]]:
        """Сгенерировать рекомендации по исправлению"""
        recommendations = []
        
        for cause in root_causes:
            if cause["type"] == "multiple_creation_paths":
                recommendations.append({
                    "priority": "high",
                    "action": "consolidate_creation_logic",
                    "description": "Объединить всю логику создания встреч в один метод",
                    "steps": [
                        "Найти все места создания встреч",
                        "Создать единый сервис для создания",
                        "Рефакторить все вызовы через единый интерфейс"
                    ]
                })
            
            elif cause["type"] == "incomplete_deletion":
                recommendations.append({
                    "priority": "critical", 
                    "action": "fix_deletion_logic",
                    "description": "Исправить логику удаления для обработки всех календарей",
                    "steps": [
                        "Найти все созданные события (manager + owner календари)",
                        "Реализовать удаление из всех календарей",
                        "Добавить проверку успешного удаления"
                    ]
                })
            
            elif cause["type"] == "event_duplication_in_code":
                recommendations.append({
                    "priority": "critical",
                    "action": "remove_code_duplication", 
                    "description": "Убрать дублирование вызовов events().insert",
                    "steps": [
                        "Найти все множественные вызовы events().insert",
                        "Оставить только один вызов на одно событие",
                        "Реализовать проверку на дублирование"
                    ]
                })
        
        return recommendations

class GoogleMeetAnalyzer:
    """Анализатор проблем с Google Meet"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history = MandatoryHistoryPersistence(project_root)
        
    def analyze_google_meet_issues(self) -> Dict[str, Any]:
        """Анализ проблем с Google Meet"""
        self.history._log("Анализирую проблемы с Google Meet")
        
        analysis = {
            "conference_creation_methods": [],
            "oauth_vs_service_account": {},
            "potential_issues": []
        }
        
        # Найти все места создания conferenceData
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Поиск conferenceData
                if 'conferenceData' in content:
                    analysis["conference_creation_methods"].append({
                        "file": str(py_file),
                        "line_count": content.count('conferenceData'),
                        "has_create_request": 'createRequest' in content,
                        "has_conference_version": 'conferenceDataVersion' in content
                    })
                
                # Анализ OAuth vs Service Account
                if 'oauth' in content.lower():
                    analysis["oauth_vs_service_account"]["oauth_usage"] = True
                    
                if 'service_account' in content.lower() or 'service account' in content.lower():
                    analysis["oauth_vs_service_account"]["service_account_usage"] = True
                
            except Exception as e:
                self.history._log(f"Ошибка анализа {py_file}: {e}", "ERROR")
        
        # Определить потенциальные проблемы
        if len(analysis["conference_creation_methods"]) > 1:
            analysis["potential_issues"].append({
                "type": "multiple_conference_creation",
                "description": "Множественные методы создания Google Meet конференций"
            })
        
        return analysis

async def diagnose_meeting_scheduler_problems(project_path: str) -> Dict[str, Any]:
    """Главная функция диагностики проблем с дублированием встреч"""
    
    # КРИТИЧЕСКИ ВАЖНО: Инициализировать систему истории
    history = MandatoryHistoryPersistence(project_path)
    
    # Создать сессию диагностики
    session_id = history._generate_id("session")
    session_data = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "problem_description": "Дублирование встреч и проблемы с Google Meet",
        "project_path": project_path
    }
    
    # Сохранить начало сессии
    history.save_session_start(session_data)
    
    try:
        # 1. Общий анализ системы
        history._log("=== PHASE 1: Анализ системы ===")
        system_analyzer = SystemAnalyzer(project_path)
        system_analysis = system_analyzer.analyze_complete_system()
        
        # 2. Специализированный анализ дублирования встреч
        history._log("=== PHASE 2: Анализ дублирования встреч ===")
        meeting_analyzer = MeetingDuplicationAnalyzer(project_path)
        meeting_analysis = meeting_analyzer.analyze_meeting_duplication()
        
        # 3. Анализ проблем с Google Meet
        history._log("=== PHASE 3: Анализ Google Meet ===")
        meet_analyzer = GoogleMeetAnalyzer(project_path)
        meet_analysis = meet_analyzer.analyze_google_meet_issues()
        
        # 4. Сохранить проблемы в базу
        for cause in meeting_analysis.get("root_causes", []):
            history.save_issue({
                "session_id": session_id,
                "description": cause["description"],
                "severity": cause["severity"],
                "component": "meeting_system"
            })
        
        # 5. Сформировать итоговый отчет
        final_result = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "status": "analysis_complete",
            "system_analysis": system_analysis,
            "meeting_duplication_analysis": meeting_analysis,
            "google_meet_analysis": meet_analysis,
            "critical_issues_count": len([c for c in meeting_analysis.get("root_causes", []) 
                                        if c.get("severity") == "critical"]),
            "fix_recommendations": meeting_analysis.get("fix_recommendations", [])
        }
        
        # ОБЯЗАТЕЛЬНО сохранить финальный результат
        result_file = history.history_root / f"diagnostic_result_{session_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        history._log(f"=== ДИАГНОСТИКА ЗАВЕРШЕНА ===")
        history._log(f"Найдено критических проблем: {final_result['critical_issues_count']}")
        history._log(f"Результат сохранен: {result_file}")
        
        return final_result
        
    except Exception as e:
        # При любой ошибке - сохранить информацию
        error_data = {
            "session_id": session_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        error_file = history.history_root / f"diagnostic_error_{session_id}.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        history._log(f"КРИТИЧЕСКАЯ ОШИБКА: {e}", "ERROR")
        raise

if __name__ == "__main__":
    # Запуск диагностики
    import asyncio
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    
    print("🛡️ Запускаю HOLISTIC DIAGNOSTIC SYSTEM v4.0")
    print("=" * 60)
    
    try:
        result = asyncio.run(diagnose_meeting_scheduler_problems(project_path))
        
        print("\n" + "=" * 60)
        print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО")
        print(f"🔍 Session ID: {result['session_id']}")
        print(f"🚨 Критических проблем: {result['critical_issues_count']}")
        print(f"📋 Рекомендаций: {len(result['fix_recommendations'])}")
        
        # Показать критические проблемы
        if result['critical_issues_count'] > 0:
            print("\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for i, cause in enumerate(result['meeting_duplication_analysis']['root_causes'], 1):
                if cause.get('severity') == 'critical':
                    print(f"  {i}. {cause['description']}")
        
        # Показать рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        for i, rec in enumerate(result['fix_recommendations'], 1):
            print(f"  {i}. [{rec['priority'].upper()}] {rec['description']}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ДИАГНОСТИКИ: {e}")
        print(traceback.format_exc())