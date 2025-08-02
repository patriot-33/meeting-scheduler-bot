#!/usr/bin/env python3
"""
🛡️ SIMPLIFIED CALENDAR DIAGNOSTIC SYSTEM v4.0
Диагностика календарных проблем без ML зависимостей (numpy, sklearn)
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback
import json
import re
import hashlib
import sqlite3

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calendar_diagnosis.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleHistoryPersistence:
    """Упрощенная система сохранения истории без зависимостей"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history_root = self.project_root / ".diagnostic_history"
        self.history_root.mkdir(exist_ok=True)
        self.db_path = self.history_root / "simple_history.db"
        self._init_database()
        
    def _init_database(self):
        """Инициализация простой БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnosis_sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT,
                problem_description TEXT,
                results TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detected_issues (
                issue_id TEXT PRIMARY KEY,
                session_id TEXT,
                issue_type TEXT,
                severity TEXT,
                description TEXT,
                fix_suggestion TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnosis_sessions(session_id)
            )
        """)
        
        conn.commit()
        conn.close()
        
    def save_session(self, session_data):
        """Сохранить сессию диагностики"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO diagnosis_sessions 
            (session_id, timestamp, problem_description, results)
            VALUES (?, ?, ?, ?)
        """, (
            session_data['session_id'],
            session_data['timestamp'],
            session_data['problem_description'],
            json.dumps(session_data.get('results', {}))
        ))
        
        conn.commit()
        conn.close()
        
    def save_issue(self, issue_data):
        """Сохранить обнаруженную проблему"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        issue_id = f"issue_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(issue_data['description']) % 10000}"
        
        cursor.execute("""
            INSERT INTO detected_issues 
            (issue_id, session_id, issue_type, severity, description, fix_suggestion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            issue_id,
            issue_data['session_id'],
            issue_data['issue_type'],
            issue_data['severity'],
            issue_data['description'],
            issue_data.get('fix_suggestion', '')
        ))
        
        conn.commit()
        conn.close()
        
        return issue_id

class SimpleCalendarDiagnostic:
    """Упрощенная диагностика календарных проблем"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.history = SimpleHistoryPersistence(project_path)
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Паттерны известных проблем
        self.known_issues = {
            'conference_type_error': {
                'patterns': ['eventHangout', 'Invalid conference type value'],
                'severity': 'high',
                'fix': 'Change eventHangout to hangoutsMeet'
            },
            'service_account_attendee_error': {
                'patterns': ['Service accounts cannot invite attendees'],
                'severity': 'high', 
                'fix': 'Remove attendee invitations for Service Account calls'
            },
            'oauth_detection_issue': {
                'patterns': ['_is_oauth_calendar', 'oauth_credentials', 'refresh_token'],
                'severity': 'medium',
                'fix': 'Improve OAuth vs Service Account detection'
            },
            'webhook_timeout': {
                'patterns': ['Connection timed out', 'webhook'],
                'severity': 'critical',
                'fix': 'Fix webhook configuration and connectivity'
            },
            'dual_calendar_sync': {
                'patterns': ['events not created', 'manager_event_id', 'owner_event_id'],
                'severity': 'high',
                'fix': 'Fix dual calendar synchronization logic'
            }
        }
        
    def run_diagnosis(self, problem_description: str) -> dict:
        """Запустить диагностику"""
        
        logger.info("🚀 Starting SIMPLIFIED CALENDAR DIAGNOSTIC SYSTEM v4.0")
        
        session_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'problem_description': problem_description
        }
        
        try:
            results = {}
            
            # 1. Анализ кода
            logger.info("🔍 Phase 1: Code Analysis")
            code_issues = self._analyze_code()
            results['code_issues'] = code_issues
            
            # 2. Анализ проблемы
            logger.info("🔍 Phase 2: Problem Analysis") 
            problem_analysis = self._analyze_problem_description(problem_description)
            results['problem_analysis'] = problem_analysis
            
            # 3. Приоритизация проблем
            logger.info("📊 Phase 3: Issue Prioritization")
            prioritized_issues = self._prioritize_issues(code_issues + problem_analysis)
            results['prioritized_issues'] = prioritized_issues
            
            # 4. Генерация исправлений
            logger.info("🔧 Phase 4: Fix Generation")
            fixes = self._generate_specific_fixes(prioritized_issues)
            results['suggested_fixes'] = fixes
            
            # 5. План действий
            logger.info("📋 Phase 5: Action Plan")
            action_plan = self._create_action_plan(prioritized_issues, fixes)
            results['action_plan'] = action_plan
            
            # Сохранить результаты
            session_data['results'] = results
            self.history.save_session(session_data)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Diagnostic failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _analyze_code(self) -> list:
        """Анализ кода календарной интеграции"""
        
        issues = []
        
        calendar_files = [
            'src/services/google_calendar_dual.py',
            'src/services/google_calendar.py',
            'src/services/meeting_service.py'
        ]
        
        for file_path in calendar_files:
            full_path = self.project_path / file_path
            if full_path.exists():
                logger.info(f"📄 Analyzing {file_path}")
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверить на известные проблемы
                file_issues = self._scan_file_for_issues(content, file_path)
                issues.extend(file_issues)
        
        return issues
    
    def _scan_file_for_issues(self, content: str, file_path: str) -> list:
        """Сканировать файл на известные проблемы"""
        
        issues = []
        
        for issue_type, issue_config in self.known_issues.items():
            for pattern in issue_config['patterns']:
                if pattern in content:
                    issue = {
                        'type': issue_type,
                        'severity': issue_config['severity'],
                        'file': file_path,
                        'pattern_found': pattern,
                        'description': f"Found {pattern} in {file_path}",
                        'suggested_fix': issue_config['fix']
                    }
                    issues.append(issue)
                    
                    # Сохранить в историю
                    self.history.save_issue({
                        'session_id': self.session_id,
                        'issue_type': issue_type,
                        'severity': issue_config['severity'],
                        'description': issue['description'],
                        'fix_suggestion': issue_config['fix']
                    })
        
        # Специфические проверки
        
        # 1. Проверка использования eventHangout
        if 'eventHangout' in content and file_path.endswith('google_calendar_dual.py'):
            issues.append({
                'type': 'conference_type_error',
                'severity': 'high',
                'file': file_path,
                'line_estimate': self._find_line_number(content, 'eventHangout'),
                'description': 'Using deprecated eventHangout instead of hangoutsMeet',
                'suggested_fix': "Change 'eventHangout' to 'hangoutsMeet' in conference type",
                'confidence': 0.95
            })
        
        # 2. Проверка OAuth detection
        if '_is_oauth_calendar' in content:
            # Поиск проблемной логики
            if 'refresh_token' not in content:
                issues.append({
                    'type': 'oauth_detection_incomplete',
                    'severity': 'medium',
                    'file': file_path,
                    'description': 'OAuth detection may be incomplete - missing refresh_token check',
                    'suggested_fix': 'Add proper refresh_token validation in OAuth detection'
                })
        
        # 3. Проверка обработки ошибок
        try_count = content.count('try:')
        except_count = content.count('except')
        if try_count > 0 and except_count / try_count < 0.8:
            issues.append({
                'type': 'insufficient_error_handling',
                'severity': 'medium',
                'file': file_path,
                'description': f'Insufficient error handling: {try_count} try blocks, {except_count} except blocks',
                'suggested_fix': 'Add comprehensive error handling for all try blocks'
            })
        
        return issues
    
    def _find_line_number(self, content: str, pattern: str) -> int:
        """Найти примерный номер строки с паттерном"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 0
    
    def _analyze_problem_description(self, description: str) -> list:
        """Анализ описания проблемы"""
        
        issues = []
        
        # Ключевые фразы и соответствующие проблемы
        problem_indicators = {
            'Invalid conference type value': {
                'type': 'conference_type_error',
                'severity': 'high',
                'fix': 'Change eventHangout to hangoutsMeet'
            },
            'Service accounts cannot invite attendees': {
                'type': 'service_account_attendee_error', 
                'severity': 'high',
                'fix': 'Remove attendee invitations for Service Account'
            },
            'events not created': {
                'type': 'event_creation_failure',
                'severity': 'critical',
                'fix': 'Fix calendar event creation logic'
            },
            'Google Meet ссылки не создаются': {
                'type': 'meet_link_failure',
                'severity': 'high',
                'fix': 'Fix Google Meet conference creation'
            },
            'OAuth vs Service Account': {
                'type': 'oauth_detection_issue',
                'severity': 'medium',
                'fix': 'Improve calendar type detection'
            }
        }
        
        for indicator, issue_config in problem_indicators.items():
            if indicator.lower() in description.lower():
                issue = {
                    'type': issue_config['type'],
                    'severity': issue_config['severity'],
                    'source': 'problem_description',
                    'description': f"Problem reported: {indicator}",
                    'suggested_fix': issue_config['fix']
                }
                issues.append(issue)
        
        return issues
    
    def _prioritize_issues(self, all_issues: list) -> list:
        """Приоритизировать проблемы"""
        
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        # Сортировать по важности
        prioritized = sorted(all_issues, 
                           key=lambda x: severity_order.get(x['severity'], 1), 
                           reverse=True)
        
        # Добавить приоритет
        for i, issue in enumerate(prioritized, 1):
            issue['priority'] = i
            
        return prioritized
    
    def _generate_specific_fixes(self, issues: list) -> dict:
        """Генерировать конкретные исправления"""
        
        fixes = {}
        
        for issue in issues:
            issue_type = issue['type']
            
            if issue_type == 'conference_type_error':
                fixes['fix_conference_type'] = {
                    'priority': 1,
                    'file': 'src/services/google_calendar_dual.py',
                    'action': 'replace_text',
                    'search': "'type': 'eventHangout'",
                    'replace': "'type': 'hangoutsMeet'",
                    'description': 'Fix conference type from eventHangout to hangoutsMeet',
                    'risk': 'low',
                    'estimated_time': '5 minutes'
                }
            
            elif issue_type == 'service_account_attendee_error':
                fixes['fix_service_account_attendees'] = {
                    'priority': 2,
                    'file': 'src/services/google_calendar_dual.py',
                    'action': 'conditional_logic',
                    'description': 'Add condition to skip attendees for Service Account calendars',
                    'risk': 'medium',
                    'estimated_time': '15 minutes'
                }
            
            elif issue_type == 'oauth_detection_issue':
                fixes['improve_oauth_detection'] = {
                    'priority': 3,
                    'file': 'src/services/google_calendar_dual.py',
                    'action': 'enhance_logic',
                    'description': 'Improve OAuth detection with refresh_token validation',
                    'risk': 'medium',
                    'estimated_time': '20 minutes'
                }
        
        return fixes
    
    def _create_action_plan(self, issues: list, fixes: dict) -> dict:
        """Создать план действий"""
        
        critical_issues = [i for i in issues if i['severity'] == 'critical']
        high_issues = [i for i in issues if i['severity'] == 'high']
        
        plan = {
            'total_issues': len(issues),
            'critical_issues': len(critical_issues),
            'high_issues': len(high_issues),
            'estimated_total_time': '1-2 hours',
            'steps': []
        }
        
        step_num = 1
        
        # Шаг 1: Критические исправления
        if 'fix_conference_type' in fixes:
            plan['steps'].append({
                'step': step_num,
                'title': 'Fix Conference Type',
                'description': fixes['fix_conference_type']['description'],
                'action': 'Apply conference type fix',
                'files': [fixes['fix_conference_type']['file']],
                'risk': 'low',
                'time': '5 minutes'
            })
            step_num += 1
        
        # Шаг 2: Service Account исправления
        if 'fix_service_account_attendees' in fixes:
            plan['steps'].append({
                'step': step_num,
                'title': 'Fix Service Account Attendees',
                'description': fixes['fix_service_account_attendees']['description'],
                'action': 'Modify attendee logic for Service Accounts',
                'files': [fixes['fix_service_account_attendees']['file']],
                'risk': 'medium',
                'time': '15 minutes'
            })
            step_num += 1
        
        # Шаг 3: OAuth улучшения
        if 'improve_oauth_detection' in fixes:
            plan['steps'].append({
                'step': step_num,
                'title': 'Improve OAuth Detection',
                'description': fixes['improve_oauth_detection']['description'],
                'action': 'Enhance OAuth vs Service Account detection',
                'files': [fixes['improve_oauth_detection']['file']],
                'risk': 'medium',
                'time': '20 minutes'
            })
            step_num += 1
        
        # Шаг 4: Тестирование
        plan['steps'].append({
            'step': step_num,
            'title': 'Test and Deploy',
            'description': 'Test changes and deploy to production',
            'action': 'Deploy and test calendar functionality',
            'risk': 'low',
            'time': '30 minutes'
        })
        
        return plan


def main():
    """Главная функция"""
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    
    problem_description = """
    Telegram бот для планирования встреч имеет проблемы с календарной интеграцией:
    1. События не создаются в календарях Google
    2. Ошибки "Invalid conference type value" 
    3. Ошибки "Service accounts cannot invite attendees"
    4. Google Meet ссылки не создаются
    5. Проблемы с определением OAuth vs Service Account календарей
    
    Логи Render показывают эти ошибки при попытке создания событий.
    """
    
    try:
        # Создать диагностическую систему
        diagnostic = SimpleCalendarDiagnostic(project_path)
        
        # Запустить диагностику
        results = diagnostic.run_diagnosis(problem_description)
        
        # Вывести результаты
        print("\n" + "="*80)
        print("🎯 РЕЗУЛЬТАТЫ УПРОЩЕННОЙ ДИАГНОСТИКИ")
        print("="*80)
        
        print(f"\n📋 Сессия: {diagnostic.session_id}")
        
        # Показать обнаруженные проблемы
        issues = results.get('prioritized_issues', [])
        print(f"\n🔍 Обнаружено проблем: {len(issues)}")
        
        for issue in issues[:5]:  # Показать топ-5 проблем
            print(f"\n   🐛 {issue.get('type', 'unknown')}")
            print(f"      Важность: {issue.get('severity', 'unknown')}")
            print(f"      Описание: {issue.get('description', 'no description')}")
            print(f"      Исправление: {issue.get('suggested_fix', 'no fix suggested')}")
        
        # План действий
        action_plan = results.get('action_plan', {})
        if action_plan.get('steps'):
            print(f"\n📋 ПЛАН ДЕЙСТВИЙ:")
            print(f"   Всего проблем: {action_plan.get('total_issues', 0)}")
            print(f"   Критических: {action_plan.get('critical_issues', 0)}")
            print(f"   Высокой важности: {action_plan.get('high_issues', 0)}")
            print(f"   Общее время: {action_plan.get('estimated_total_time', 'unknown')}")
            
            for step in action_plan['steps']:
                print(f"\n   Шаг {step['step']}: {step['title']}")
                print(f"      {step['description']}")
                print(f"      Время: {step.get('time', 'unknown')}")
                print(f"      Риск: {step.get('risk', 'unknown')}")
        
        # Конкретные исправления
        fixes = results.get('suggested_fixes', {})
        if fixes:
            print(f"\n🔧 КОНКРЕТНЫЕ ИСПРАВЛЕНИЯ:")
            for fix_name, fix_details in fixes.items():
                print(f"\n   {fix_name}:")
                print(f"      Файл: {fix_details.get('file', 'unknown')}")
                print(f"      Действие: {fix_details.get('description', 'unknown')}")
                if 'search' in fix_details and 'replace' in fix_details:
                    print(f"      Заменить: '{fix_details['search']}'")
                    print(f"      На: '{fix_details['replace']}'")
        
        # Сохранить детальный отчет
        report_file = Path(project_path) / "simple_diagnostic_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Детальный отчет сохранен: {report_file}")
        print("\n✅ Упрощенная диагностика завершена!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Diagnostic system failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    # Запустить упрощенную диагностику
    results = main()