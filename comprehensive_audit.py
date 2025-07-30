#!/usr/bin/env python3
"""
Comprehensive Audit Script for Meeting Scheduler Bot
Проверяет все возможные ошибки включая проблемы с сохранением данных после деплоя
"""

import os
import sys
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
import logging

# Добавляем src в путь для импорта
sys.path.append('/Users/evgenii/meeting-scheduler-bot/src')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveAudit:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
        
    def log_issue(self, severity, category, description, fix_applied=None):
        issue = {
            'severity': severity,
            'category': category, 
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'fix_applied': fix_applied
        }
        
        if severity == 'CRITICAL':
            self.issues.append(issue)
        else:
            self.warnings.append(issue)
            
        if fix_applied:
            self.fixes_applied.append(issue)
            
        print(f"[{severity}] {category}: {description}")
        if fix_applied:
            print(f"  ✅ Fix applied: {fix_applied}")

    def check_environment_variables(self):
        """Проверка всех переменных окружения"""
        print("\n🔍 Checking Environment Variables...")
        
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'ADMIN_TELEGRAM_IDS', 
            'DATABASE_URL',
            'GOOGLE_CALENDAR_ID_1',
            'GOOGLE_CALENDAR_ID_2'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.log_issue('CRITICAL', 'Environment', f'Missing required variable: {var}')
            elif var == 'TELEGRAM_BOT_TOKEN' and len(value) < 20:
                self.log_issue('CRITICAL', 'Environment', f'Invalid {var}: too short')
            elif var == 'ADMIN_TELEGRAM_IDS' and not value.isdigit():
                self.log_issue('WARNING', 'Environment', f'Invalid {var}: should be numeric')
                
        # Проверка optional переменных
        optional_vars = ['WEBHOOK_URL', 'GOOGLE_SERVICE_ACCOUNT_FILE']
        for var in optional_vars:
            value = os.getenv(var)
            if not value:
                self.log_issue('WARNING', 'Environment', f'Optional variable not set: {var}')

    def check_file_structure(self):
        """Проверка структуры файлов проекта"""
        print("\n🔍 Checking File Structure...")
        
        required_files = [
            '/Users/evgenii/meeting-scheduler-bot/src/main.py',
            '/Users/evgenii/meeting-scheduler-bot/src/config.py',
            '/Users/evgenii/meeting-scheduler-bot/src/database.py',
            '/Users/evgenii/meeting-scheduler-bot/requirements.txt',
            '/Users/evgenii/meeting-scheduler-bot/Dockerfile',
            '/Users/evgenii/meeting-scheduler-bot/service_account_key.json'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                self.log_issue('CRITICAL', 'File Structure', f'Missing required file: {file_path}')
            else:
                # Проверка размера файла
                size = os.path.getsize(file_path)
                if size == 0:
                    self.log_issue('CRITICAL', 'File Structure', f'Empty file: {file_path}')
                elif file_path.endswith('.json') and size < 100:
                    self.log_issue('WARNING', 'File Structure', f'Suspiciously small JSON file: {file_path}')

    def check_google_service_account(self):
        """Проверка Google Service Account файла"""
        print("\n🔍 Checking Google Service Account...")
        
        service_file = '/Users/evgenii/meeting-scheduler-bot/service_account_key.json'
        try:
            with open(service_file, 'r') as f:
                service_data = json.load(f)
                
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            for field in required_fields:
                if field not in service_data:
                    self.log_issue('CRITICAL', 'Google Auth', f'Missing field in service account: {field}')
                elif not service_data[field]:
                    self.log_issue('CRITICAL', 'Google Auth', f'Empty field in service account: {field}')
                    
            # Проверка формата private_key
            if 'private_key' in service_data:
                private_key = service_data['private_key']
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                    self.log_issue('CRITICAL', 'Google Auth', 'Invalid private key format')
                    
        except Exception as e:
            self.log_issue('CRITICAL', 'Google Auth', f'Cannot read service account file: {e}')

    def check_database_migration_safety(self):
        """Проверка безопасности миграций базы данных"""
        print("\n🔍 Checking Database Migration Safety...")
        
        # Проверяем есть ли данные в текущей базе
        db_path = '/Users/evgenii/meeting-scheduler-bot/test.db'
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Проверяем каждую таблицу на наличие данных
                tables = ['users', 'owner_availability', 'meetings', 'reminders']
                data_found = False
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            data_found = True
                            self.log_issue('WARNING', 'Data Migration', 
                                         f'Table {table} contains {count} records that may be lost on deployment')
                    except sqlite3.OperationalError:
                        self.log_issue('WARNING', 'Data Migration', f'Table {table} does not exist yet')
                
                if data_found:
                    self.log_issue('CRITICAL', 'Data Migration', 
                                 'Local SQLite database contains data that will be lost when switching to PostgreSQL on deployment')
                
                conn.close()
                
            except Exception as e:
                self.log_issue('WARNING', 'Data Migration', f'Cannot check local database: {e}')

    def check_enum_compatibility(self):
        """Проверка совместимости enum с PostgreSQL"""
        print("\n🔍 Checking Enum Compatibility...")
        
        try:
            # Импортируем модели базы данных
            from database import UserRole, UserStatus, MeetingStatus, Department
            
            # Проверяем что все enum имеют правильные значения
            enums_to_check = [
                ('UserRole', UserRole, ['owner', 'manager', 'pending']),
                ('UserStatus', UserStatus, ['active', 'vacation', 'sick_leave', 'business_trip', 'deleted']),
                ('MeetingStatus', MeetingStatus, ['scheduled', 'completed', 'cancelled', 'no_show']),
                ('Department', Department, ['Фарм отдел', 'Фин отдел', 'HR отдел', 'Тех отдел', 'ИТ отдел', 'Биздев отдел', 'Геймдев проект'])
            ]
            
            for enum_name, enum_class, expected_values in enums_to_check:
                actual_values = [e.value for e in enum_class]
                
                # Проверяем что все ожидаемые значения присутствуют
                for expected in expected_values:
                    if expected not in actual_values:
                        self.log_issue('CRITICAL', 'Enum Compatibility', 
                                     f'{enum_name} missing expected value: {expected}')
                
                # Проверяем на подозрительные символы в enum значениях
                for value in actual_values:
                    if not isinstance(value, str):
                        self.log_issue('WARNING', 'Enum Compatibility', 
                                     f'{enum_name} has non-string value: {value}')
                    elif len(value) > 20:
                        self.log_issue('WARNING', 'Enum Compatibility', 
                                     f'{enum_name} has very long value: {value}')
                        
        except ImportError as e:
            self.log_issue('CRITICAL', 'Enum Compatibility', f'Cannot import database models: {e}')

    def check_deployment_configuration(self):
        """Проверка конфигурации деплоя"""
        print("\n🔍 Checking Deployment Configuration...")
        
        # Проверяем Dockerfile
        dockerfile_path = '/Users/evgenii/meeting-scheduler-bot/Dockerfile'
        try:
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
                
            if 'PYTHONPATH=' not in dockerfile_content:
                self.log_issue('WARNING', 'Deployment', 'Dockerfile missing PYTHONPATH configuration')
                
            if 'WORKDIR /app/src' not in dockerfile_content:
                self.log_issue('WARNING', 'Deployment', 'Dockerfile missing correct WORKDIR')
                
            if 'python main.py' not in dockerfile_content:
                self.log_issue('WARNING', 'Deployment', 'Dockerfile has incorrect start command')
                
        except Exception as e:
            self.log_issue('CRITICAL', 'Deployment', f'Cannot read Dockerfile: {e}')
            
        # Проверяем render.yaml
        render_yaml_path = '/Users/evgenii/meeting-scheduler-bot/render.yaml'
        try:
            with open(render_yaml_path, 'r') as f:
                render_content = f.read()
                
            if 'cd src && python main.py' not in render_content:
                self.log_issue('CRITICAL', 'Deployment', 'render.yaml has incorrect start command')
                
            if 'PYTHONPATH' not in render_content:
                self.log_issue('WARNING', 'Deployment', 'render.yaml missing PYTHONPATH configuration')
                
        except Exception as e:
            self.log_issue('CRITICAL', 'Deployment', f'Cannot read render.yaml: {e}')

    def check_import_structure(self):
        """Проверка структуры импортов"""
        print("\n🔍 Checking Import Structure...")
        
        # Проверяем основные файлы на правильность импортов
        files_to_check = [
            '/Users/evgenii/meeting-scheduler-bot/src/main.py',
            '/Users/evgenii/meeting-scheduler-bot/src/handlers/admin.py',
            '/Users/evgenii/meeting-scheduler-bot/src/services/google_calendar.py'
        ]
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Проверяем на старые импорты с src.
                if 'from src.' in content:
                    self.log_issue('CRITICAL', 'Import Structure', 
                                 f'File {file_path} still contains old "from src." imports')
                    
                # Проверяем на правильные относительные импорты
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if line.strip().startswith('from src.'):
                        self.log_issue('CRITICAL', 'Import Structure', 
                                     f'File {file_path}:{i} has incorrect import: {line.strip()}')
                        
            except Exception as e:
                self.log_issue('WARNING', 'Import Structure', f'Cannot check imports in {file_path}: {e}')

    def check_data_persistence_strategy(self):
        """Проверка стратегии сохранения данных"""
        print("\n🔍 Checking Data Persistence Strategy...")
        
        # Проверяем наличие скриптов миграции
        migration_files = [
            '/Users/evgenii/meeting-scheduler-bot/hotfix_enum.py',
            '/Users/evgenii/meeting-scheduler-bot/add_email_field_migration.py'
        ]
        
        migration_found = False
        for file_path in migration_files:
            if os.path.exists(file_path):
                migration_found = True
                break
                
        if not migration_found:
            self.log_issue('WARNING', 'Data Persistence', 
                         'No migration scripts found - data may be lost on schema changes')
        
        # Проверяем стратегию backup/restore данных
        backup_strategy_exists = False
        backup_files = ['backup_data.py', 'export_data.py', 'data_migration.py']
        
        for backup_file in backup_files:
            if os.path.exists(f'/Users/evgenii/meeting-scheduler-bot/{backup_file}'):
                backup_strategy_exists = True
                break
                
        if not backup_strategy_exists:
            self.log_issue('CRITICAL', 'Data Persistence', 
                         'No backup/restore strategy found - approved managers and slots will be lost on deployment')

    def check_google_calendar_permissions(self):
        """Проверка разрешений Google Calendar"""
        print("\n🔍 Checking Google Calendar Permissions...")
        
        try:
            # Пытаемся инициализировать Google Calendar API
            from services.google_calendar import GoogleCalendarService
            
            calendar_service = GoogleCalendarService()
            
            # Проверяем доступ к календарю
            calendar_id = os.getenv('GOOGLE_CALENDAR_ID_1', 'plantatorbob@gmail.com')
            
            # Эту проверку делаем только если есть интернет
            self.log_issue('WARNING', 'Google Calendar', 
                         'Cannot verify Google Calendar permissions without running the service')
                         
        except ImportError as e:
            self.log_issue('CRITICAL', 'Google Calendar', f'Cannot import Google Calendar service: {e}')
        except Exception as e:
            self.log_issue('WARNING', 'Google Calendar', f'Google Calendar service check failed: {e}')

    def create_data_backup_script(self):
        """Создаем скрипт для backup данных"""
        print("\n🔧 Creating Data Backup Script...")
        
        backup_script = '''#!/usr/bin/env python3
"""
Data Backup Script for Meeting Scheduler Bot
Экспортирует критические данные перед деплоем
"""

import sys
import json
import sqlite3
from datetime import datetime

def backup_data():
    """Экспорт данных из SQLite в JSON"""
    
    db_path = 'test.db'
    backup_data = {
        'backup_timestamp': datetime.now().isoformat(),
        'users': [],
        'owner_availability': [],
        'meetings': [],
        'reminders': []
    }
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Позволяет получать результаты как dict
        cursor = conn.cursor()
        
        # Экспорт пользователей
        cursor.execute("SELECT * FROM users")
        backup_data['users'] = [dict(row) for row in cursor.fetchall()]
        
        # Экспорт доступности владельцев
        cursor.execute("SELECT * FROM owner_availability")
        backup_data['owner_availability'] = [dict(row) for row in cursor.fetchall()]
        
        # Экспорт встреч
        cursor.execute("SELECT * FROM meetings")
        backup_data['meetings'] = [dict(row) for row in cursor.fetchall()]
        
        # Экспорт напоминаний
        cursor.execute("SELECT * FROM reminders")
        backup_data['reminders'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Сохраняем backup
        backup_filename = f'data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
        print(f"✅ Data backed up to {backup_filename}")
        
        # Показываем статистику
        total_records = sum(len(backup_data[key]) for key in ['users', 'owner_availability', 'meetings', 'reminders'])
        print(f"📊 Backed up {total_records} total records:")
        for table, records in backup_data.items():
            if table != 'backup_timestamp' and records:
                print(f"  - {table}: {len(records)} records")
                
        return backup_filename
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

if __name__ == "__main__":
    backup_data()
'''
        
        backup_script_path = '/Users/evgenii/meeting-scheduler-bot/backup_data.py'
        with open(backup_script_path, 'w') as f:
            f.write(backup_script)
            
        # Делаем файл исполняемым
        os.chmod(backup_script_path, 0o755)
        
        self.log_issue('INFO', 'Data Persistence', 
                     f'Created backup script: {backup_script_path}',
                     'Data backup script created for pre-deployment use')

    def create_restore_script(self):
        """Создаем скрипт для восстановления данных"""
        print("\n🔧 Creating Data Restore Script...")
        
        restore_script = '''#!/usr/bin/env python3
"""
Data Restore Script for Meeting Scheduler Bot
Восстанавливает данные из backup после деплоя
"""

import sys
import json
import os
from datetime import datetime

# Добавляем src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def restore_data(backup_file):
    """Восстановление данных из JSON backup"""
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    try:
        from database import get_db, User, OwnerAvailability, Meeting, Reminder
        from database import UserRole, UserStatus, MeetingStatus, Department
        from sqlalchemy.exc import IntegrityError
        
        # Загружаем backup
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
            
        print(f"📂 Loading backup from {backup_data.get('backup_timestamp', 'unknown time')}")
        
        with get_db() as db:
            restored = {'users': 0, 'slots': 0, 'meetings': 0, 'reminders': 0}
            
            # Восстанавливаем пользователей
            for user_data in backup_data.get('users', []):
                try:
                    # Проверяем, не существует ли уже пользователь
                    existing = db.query(User).filter_by(telegram_id=user_data['telegram_id']).first()
                    if existing:
                        print(f"⚠️ User {user_data['telegram_id']} already exists, skipping")
                        continue
                        
                    user = User(
                        telegram_id=user_data['telegram_id'],
                        telegram_username=user_data.get('telegram_username'),
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],  
                        email=user_data.get('email'),
                        department=Department(user_data['department']),
                        role=UserRole(user_data['role']) if user_data['role'] else UserRole.PENDING,
                        status=UserStatus(user_data['status']) if user_data['status'] else UserStatus.ACTIVE
                    )
                    db.add(user)
                    restored['users'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to restore user {user_data.get('telegram_id', 'unknown')}: {e}")
            
            # Коммитим пользователей сначала, чтобы получить их ID
            try:
                db.commit()
            except IntegrityError as e:
                print(f"⚠️ Some users already exist: {e}")
                db.rollback()
                
            # Восстанавливаем слоты доступности
            for slot_data in backup_data.get('owner_availability', []):
                try:
                    # Находим пользователя по telegram_id из backup
                    owner = db.query(User).filter_by(telegram_id=slot_data['owner_id']).first()
                    if not owner:
                        print(f"⚠️ Owner not found for slot, skipping")
                        continue
                        
                    slot = OwnerAvailability(
                        owner_id=owner.id,
                        day_of_week=slot_data['day_of_week'],
                        time_slot=slot_data['time_slot'],
                        is_active=slot_data.get('is_active', True)
                    )
                    db.add(slot)
                    restored['slots'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to restore slot: {e}")
            
            # Восстанавливаем встречи
            for meeting_data in backup_data.get('meetings', []):
                try:
                    manager = db.query(User).filter_by(telegram_id=meeting_data['manager_id']).first()
                    if not manager:
                        continue
                        
                    meeting = Meeting(
                        manager_id=manager.id,
                        scheduled_time=datetime.fromisoformat(meeting_data['scheduled_time']),
                        google_event_id=meeting_data.get('google_event_id'),
                        google_meet_link=meeting_data.get('google_meet_link'),
                        status=MeetingStatus(meeting_data['status']) if meeting_data['status'] else MeetingStatus.SCHEDULED
                    )
                    db.add(meeting)
                    restored['meetings'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to restore meeting: {e}")
            
            # Коммитим все изменения
            db.commit()
            
            print(f"✅ Restore completed:")
            for table, count in restored.items():
                if count > 0:
                    print(f"  - {table}: {count} records restored")
                    
            return True
            
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_data.py <backup_file.json>")
        sys.exit(1)
        
    restore_data(sys.argv[1])
'''
        
        restore_script_path = '/Users/evgenii/meeting-scheduler-bot/restore_data.py'
        with open(restore_script_path, 'w') as f:
            f.write(restore_script)
            
        os.chmod(restore_script_path, 0o755)
        
        self.log_issue('INFO', 'Data Persistence', 
                     f'Created restore script: {restore_script_path}',
                     'Data restore script created for post-deployment use')

    def run_full_audit(self):
        """Запуск полного аудита"""
        print("🚀 Starting Comprehensive Audit of Meeting Scheduler Bot")
        print("=" * 70)
        
        # Загружаем .env файл
        try:
            from dotenv import load_dotenv
            load_dotenv('/Users/evgenii/meeting-scheduler-bot/.env')
        except:
            print("⚠️ Cannot load .env file")
        
        # Запускаем все проверки
        self.check_environment_variables()
        self.check_file_structure()
        self.check_google_service_account()
        self.check_database_migration_safety()
        self.check_enum_compatibility()
        self.check_deployment_configuration()
        self.check_import_structure()
        self.check_data_persistence_strategy()
        self.check_google_calendar_permissions()
        
        # Создаем необходимые скрипты
        self.create_data_backup_script()
        self.create_restore_script()
        
        # Генерируем финальный отчет
        self.generate_final_report()

    def generate_final_report(self):
        """Генерация финального отчета"""
        print("\n" + "=" * 70)
        print("📋 COMPREHENSIVE AUDIT REPORT")
        print("=" * 70)
        
        print(f"\n🔴 CRITICAL ISSUES: {len(self.issues)}")
        for issue in self.issues:
            print(f"  ❌ [{issue['category']}] {issue['description']}")
            
        print(f"\n🟡 WARNINGS: {len(self.warnings)}")
        for warning in self.warnings:
            print(f"  ⚠️ [{warning['category']}] {warning['description']}")
            
        print(f"\n✅ FIXES APPLIED: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"  🔧 [{fix['category']}] {fix['fix_applied']}")
            
        # Сохраняем отчет в файл
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'critical_issues': self.issues,
            'warnings': self.warnings,
            'fixes_applied': self.fixes_applied,
            'summary': {
                'critical_count': len(self.issues),
                'warning_count': len(self.warnings),
                'fixes_count': len(self.fixes_applied),
                'deployment_ready': len(self.issues) == 0
            }
        }
        
        report_file = '/Users/evgenii/meeting-scheduler-bot/comprehensive_audit_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 Full report saved to: {report_file}")
        
        if len(self.issues) == 0:
            print("\n🎉 DEPLOYMENT READY! All critical issues resolved.")
        else:
            print(f"\n⚠️ DEPLOYMENT BLOCKED: {len(self.issues)} critical issues must be resolved first.")
            
        return report

if __name__ == "__main__":
    audit = ComprehensiveAudit()
    audit.run_full_audit()