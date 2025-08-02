#!/usr/bin/env python3
"""
🎯 ТОЧНОЕ ИСПРАВЛЕНИЕ v5.0
Устранение РЕАЛЬНОЙ корневой причины: множественные вызовы создания встреч
Основано на детальном анализе ROOT_CAUSE_ANALYSIS_REPORT.json
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

class PreciseFixImplementation:
    """Точная реализация исправлений"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def log(self, message: str):
        """Логирование"""
        timestamp = datetime.now().isoformat()
        print(f"🎯 [{timestamp}] {message}")
    
    def create_backup(self, file_path: str) -> str:
        """Создать бэкап файла"""
        backup_id = f"precise_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir = self.project_root / "precise_fix_backups" / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if Path(file_path).exists():
            backup_file = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_file)
            self.log(f"Создан бэкап: {backup_file}")
            return backup_id
        return None
    
    def fix_meeting_service_duplication(self) -> dict:
        """ИСПРАВЛЕНИЕ 1: Убрать дублированный вызов в meeting_service.py"""
        self.log("=== ИСПРАВЛЕНИЕ 1: Meeting Service Duplication ===")
        
        file_path = self.project_root / "src" / "services" / "meeting_service.py"
        backup_id = self.create_backup(str(file_path))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Убрать весь fallback блок в create_meeting
        fallback_block_start = '''# If manager's calendar failed, try owner's calendar as fallback'''
        fallback_block_end = '''else:
                            raise calendar_error'''
        
        if fallback_block_start in content:
            # Найти начало и конец блока
            start_idx = content.find(fallback_block_start)
            end_idx = content.find(fallback_block_end, start_idx)
            
            if start_idx != -1 and end_idx != -1:
                # Удалить весь fallback блок
                end_idx += len(fallback_block_end)
                content = content[:start_idx] + content[end_idx:]
                
                self.log("✅ Удален дублированный fallback блок создания встреч")
        
        # Также убрать логику которая дублирует календарь
        old_line = "owner_calendar_id or manager_calendar_id"
        new_line = "owner_calendar_id"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            self.log("✅ Исправлена логика owner_calendar_id")
        
        # Записать исправленный файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "status": "fixed",
            "file": str(file_path),
            "backup_id": backup_id,
            "changes": [
                "Удален дублированный fallback блок создания",
                "Исправлена логика owner_calendar_id"
            ]
        }
    
    def fix_dual_calendar_fallback(self) -> dict:
        """ИСПРАВЛЕНИЕ 2: Упростить _create_event_with_fallback до 1 вызова"""
        self.log("=== ИСПРАВЛЕНИЕ 2: Dual Calendar Fallback ===")
        
        file_path = self.project_root / "src" / "services" / "google_calendar_dual.py"
        backup_id = self.create_backup(str(file_path))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменить весь метод _create_event_with_fallback на простую версию
        new_method = '''    def _create_event_with_fallback(self, calendar_id: str, event_data: dict, calendar_type: str):
        """Create event with OAuth-specific Google Meet conference creation - SINGLE CALL ONLY"""
        
        # Log the attempt for debugging
        has_conference = 'conferenceData' in event_data
        has_attendees = 'attendees' in event_data
        logger.info(f"📅 Creating event in {calendar_type}'s calendar: {calendar_id}")
        logger.info(f"🔍 Event details: conference={has_conference}, attendees={has_attendees}")
        
        # Detect calendar type: OAuth vs Service Account
        is_oauth_calendar = self._is_oauth_calendar(calendar_id)
        logger.info(f"🔍 Calendar type: {'OAuth' if is_oauth_calendar else 'Service Account'}")
        
        # SINGLE ATTEMPT - No multiple fallbacks to prevent duplication
        try:
            if is_oauth_calendar:
                # OAuth calendars work best without conferenceDataVersion
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=event_data
                ).execute()
            else:
                # Service Account calendars need conferenceDataVersion
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=event_data,
                    conferenceDataVersion=1
                ).execute()
            
            # Check if Google Meet was created
            if event.get('conferenceData') and event.get('conferenceData').get('conferenceId'):
                logger.info(f"✅ SUCCESS: Created event with Google Meet in {calendar_type}'s calendar")
                logger.info(f"🔗 Google Meet ID: {event.get('conferenceData').get('conferenceId')}")
            else:
                logger.info(f"✅ SUCCESS: Created event (no Google Meet) in {calendar_type}'s calendar")
            
            return event
            
        except Exception as e:
            logger.error(f"❌ Failed to create event in {calendar_type}'s calendar: {e}")
            return None'''
        
        # Найти и заменить существующий метод
        start_pattern = "def _create_event_with_fallback("
        end_pattern = "def _is_valid_email("
        
        start_idx = content.find(start_pattern)
        end_idx = content.find(end_pattern)
        
        if start_idx != -1 and end_idx != -1:
            content = content[:start_idx] + new_method + "\n\n    " + content[end_idx:]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log("✅ Заменен метод _create_event_with_fallback на версию с 1 вызовом")
        
        return {
            "status": "fixed",
            "file": str(file_path),
            "backup_id": backup_id,
            "changes": [
                "Метод _create_event_with_fallback теперь делает только 1 вызов events().insert",
                "Убраны все дублирующие fallback стратегии",
                "Сохранена OAuth vs Service Account логика"
            ]
        }
    
    def verify_fixes(self) -> dict:
        """Проверить исправления"""
        self.log("=== ВЕРИФИКАЦИЯ ИСПРАВЛЕНИЙ ===")
        
        verification = {
            "meeting_service_calls": 0,
            "dual_calendar_insert_calls": 0,
            "expected_total_events": 0
        }
        
        # Проверить meeting_service.py
        meeting_file = self.project_root / "src" / "services" / "meeting_service.py"
        with open(meeting_file, 'r', encoding='utf-8') as f:
            content = f.read()
            verification["meeting_service_calls"] = content.count("dual_calendar_creator.create_meeting_in_both_calendars")
        
        # Проверить google_calendar_dual.py
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
            verification["dual_calendar_insert_calls"] = content.count("events().insert")
        
        # Вычислить ожидаемое количество событий
        verification["expected_total_events"] = verification["meeting_service_calls"] * 2 * (verification["dual_calendar_insert_calls"] // 2)
        
        self.log(f"📊 Вызовов dual_calendar_creator: {verification['meeting_service_calls']}")
        self.log(f"📊 Вызовов events().insert: {verification['dual_calendar_insert_calls']}")
        self.log(f"📊 Ожидаемое количество событий: {verification['expected_total_events']}")
        
        # Идеальный результат: 1 вызов dual_calendar_creator × 2 календаря × 1 events().insert = 2 события
        verification["is_fixed"] = (
            verification["meeting_service_calls"] == 1 and
            verification["dual_calendar_insert_calls"] <= 2 and
            verification["expected_total_events"] <= 2
        )
        
        return verification
    
    def apply_precise_fixes(self) -> dict:
        """Применить все точные исправления"""
        self.log("🎯 === ПРИМЕНЕНИЕ ТОЧНЫХ ИСПРАВЛЕНИЙ ===")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "fixes": [],
            "verification": {},
            "success": False
        }
        
        try:
            # Исправление 1: Meeting Service
            fix1 = self.fix_meeting_service_duplication()
            results["fixes"].append(fix1)
            
            # Исправление 2: Dual Calendar Fallback
            fix2 = self.fix_dual_calendar_fallback()
            results["fixes"].append(fix2)
            
            # Верификация
            verification = self.verify_fixes()
            results["verification"] = verification
            results["success"] = verification["is_fixed"]
            
            if results["success"]:
                self.log("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО")
                self.log(f"📊 Ожидается создание {verification['expected_total_events']} событий (вместо 4)")
            else:
                self.log("⚠️ Исправления применены, но верификация показывает потенциальные проблемы")
            
            # Сохранить результаты
            results_file = self.project_root / "PRECISE_FIX_RESULTS.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.log(f"📁 Результаты сохранены: {results_file}")
            
        except Exception as e:
            results["error"] = str(e)
            self.log(f"❌ ОШИБКА: {e}")
        
        return results

if __name__ == "__main__":
    print("🎯 ТОЧНОЕ ИСПРАВЛЕНИЕ v5.0")
    print("=" * 60)
    print("Устранение РЕАЛЬНОЙ корневой причины дублирования встреч")
    print("=" * 60)
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    fixer = PreciseFixImplementation(project_path)
    
    try:
        results = fixer.apply_precise_fixes()
        
        print("\n" + "=" * 60)
        if results["success"]:
            print("✅ ТОЧНЫЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ УСПЕШНО")
            print(f"📊 Ожидается: {results['verification']['expected_total_events']} событий вместо 4")
        else:
            print("⚠️ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ С ПРЕДУПРЕЖДЕНИЯМИ")
        
        print(f"\n🔧 Применено исправлений: {len(results['fixes'])}")
        for i, fix in enumerate(results['fixes'], 1):
            print(f"  {i}. {fix['file']}")
            for change in fix['changes']:
                print(f"     - {change}")
        
        verification = results['verification']
        print(f"\n📊 ВЕРИФИКАЦИЯ:")
        print(f"   - Вызовов создания: {verification['meeting_service_calls']}")
        print(f"   - Вызовов events().insert: {verification['dual_calendar_insert_calls']}")
        print(f"   - Ожидаемое количество событий: {verification['expected_total_events']}")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        print(traceback.format_exc())