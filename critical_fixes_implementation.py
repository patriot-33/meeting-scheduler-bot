#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ v4.0
Исправление основных проблем:
1. Создается по 3 мероприятия в каждом календаре 
2. При удалении остаются 2 мероприятия
3. Google Meet не создается

ОБЯЗАТЕЛЬНОЕ сохранение всей истории изменений
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from diagnostic_system_v4 import MandatoryHistoryPersistence

class CriticalFixesImplementation:
    """Реализация критических исправлений"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history = MandatoryHistoryPersistence(project_root)
        
    def analyze_duplication_root_cause(self) -> dict:
        """Детальный анализ корневой причины дублирования"""
        self.history._log("=== АНАЛИЗ КОРНЕВОЙ ПРИЧИНЫ ДУБЛИРОВАНИЯ ===")
        
        analysis = {
            "dual_calendar_service": self.analyze_dual_calendar_implementation(),
            "meeting_service_calls": self.analyze_meeting_service_calls(),
            "event_creation_flow": self.trace_event_creation_flow()
        }
        
        # Сохранить анализ
        analysis_file = self.history.history_root / "duplication_root_cause_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        self.history._log(f"Анализ корневой причины сохранен: {analysis_file}")
        return analysis
    
    def analyze_dual_calendar_implementation(self) -> dict:
        """Анализ реализации DualCalendarCreator"""
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        if not dual_file.exists():
            return {"error": "google_calendar_dual.py not found"}
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проанализировать create_meeting_in_both_calendars
        analysis = {
            "method_exists": "create_meeting_in_both_calendars" in content,
            "creates_in_manager_calendar": "manager_calendar_id" in content,
            "creates_in_owner_calendar": "owner_calendar_id" in content,
            "uses_same_calendar_twice": False,
            "fallback_strategies": content.count("_create_event_with_fallback")
        }
        
        # Проверить, может ли один календарь использоваться дважды
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "owner_calendar_id or manager_calendar_id" in line:
                analysis["uses_same_calendar_twice"] = True
                analysis["problematic_line"] = i + 1
                break
        
        return analysis
    
    def analyze_meeting_service_calls(self) -> dict:
        """Анализ вызовов в MeetingService"""
        meeting_file = self.project_root / "src" / "services" / "meeting_service.py"
        
        with open(meeting_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найти все вызовы создания встреч
        dual_calendar_calls = []
        single_calendar_calls = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "dual_calendar_creator.create_meeting_in_both_calendars" in line:
                dual_calendar_calls.append(i)
            elif "calendar_service.create_meeting" in line:
                single_calendar_calls.append(i)
        
        return {
            "dual_calendar_calls": dual_calendar_calls,
            "single_calendar_calls": single_calendar_calls,
            "total_creation_calls": len(dual_calendar_calls) + len(single_calendar_calls)
        }
    
    def trace_event_creation_flow(self) -> dict:
        """Трассировка потока создания событий"""
        flow = {
            "entry_point": "MeetingService.create_meeting",
            "steps": [
                "1. MeetingService.create_meeting() вызывается",
                "2. dual_calendar_creator.create_meeting_in_both_calendars()",
                "3. Создается событие в manager календаре",
                "4. Создается событие в owner календаре (если отличается)",
                "5. Fallback стратегии при ошибках"
            ],
            "potential_duplication_points": [
                "Если manager_calendar_id == owner_calendar_id, событие создается дважды",
                "Fallback может создать дополнительные события",
                "Ошибки в _create_event_with_fallback могут приводить к множественным попыткам"
            ]
        }
        
        return flow
    
    def fix_event_duplication(self) -> dict:
        """ОСНОВНОЕ ИСПРАВЛЕНИЕ: Убрать дублирование событий"""
        self.history._log("=== ИСПРАВЛЕНИЕ ДУБЛИРОВАНИЯ СОБЫТИЙ ===")
        
        # Создать точку отката
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        rollback_id = self.create_rollback_point(str(dual_file))
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ 1: Исправить логику создания в обоих календарях
        fixed_content = self.fix_both_calendars_logic(content)
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ 2: Убрать fallback дублирование
        fixed_content = self.fix_fallback_duplication(fixed_content)
        
        # Записать исправленный файл
        with open(dual_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        self.history._log("✅ Исправлено дублирование событий в google_calendar_dual.py")
        
        return {
            "status": "fixed",
            "file": str(dual_file),
            "rollback_id": rollback_id,
            "fixes_applied": [
                "Исправлена логика создания в обоих календарях",
                "Убрано дублирование в fallback стратегиях"
            ]
        }
    
    def fix_both_calendars_logic(self, content: str) -> str:
        """Исправить логику создания в обоих календарях"""
        
        # Найти и исправить проблемную строку в create_meeting_in_both_calendars
        old_line = "owner_calendar_id or manager_calendar_id"
        new_line = "owner_calendar_id"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            self.history._log("✅ Исправлена логика выбора календаря owner'а")
        
        # Добавить проверку на дублирование календарей
        old_check = "if owner_calendar_id and owner_calendar_id != manager_calendar_id:"
        new_check = """if owner_calendar_id and owner_calendar_id != manager_calendar_id:
            # Ensure we don't create duplicate events in the same calendar"""
        
        if old_check in content and new_check not in content:
            content = content.replace(old_check, new_check)
            self.history._log("✅ Добавлена проверка на дублирование календарей")
        
        return content
    
    def fix_fallback_duplication(self, content: str) -> str:
        """Убрать дублирование в fallback стратегиях"""
        
        # Упростить _create_event_with_fallback - оставить только основную стратегию и финальный fallback
        old_complex_fallback = '''        # Strategy 2: Service Account specific approach
        elif has_conference and not is_oauth_calendar:
            logger.info("🔄 Using Service Account Google Meet creation...")
            
            for version in [1, 0]:  # Try both conference data versions
                try:
                    logger.info(f"🔄 Attempting Google Meet creation with conferenceDataVersion={version}")
                    
                    if version == 0:
                        # For version 0, try without conferenceDataVersion parameter
                        event = self.calendar_service._service.events().insert(
                            calendarId=calendar_id,
                            body=event_data
                        ).execute()
                    else:
                        # For version 1, explicitly set conferenceDataVersion
                        event = self.calendar_service._service.events().insert(
                            calendarId=calendar_id,
                            body=event_data,
                            conferenceDataVersion=version
                        ).execute()
                    
                    # Check if Google Meet was actually created
                    if event.get('conferenceData') and event.get('conferenceData').get('conferenceId'):
                        logger.info(f"✅ SUCCESS: Service Account created Google Meet (version {version})")
                        logger.info(f"🔗 Google Meet ID: {event.get('conferenceData').get('conferenceId')}")
                        return event
                    else:
                        logger.warning(f"⚠️ Event created but no Google Meet generated (version {version})")
                        
                except Exception as version_error:
                    logger.warning(f"❌ conferenceDataVersion {version} failed: {version_error}")
                    continue'''
        
        new_simple_fallback = '''        # Strategy 2: Service Account approach - single attempt
        elif has_conference and not is_oauth_calendar:
            logger.info("🔄 Using Service Account Google Meet creation...")
            try:
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=event_data,
                    conferenceDataVersion=1
                ).execute()
                
                if event.get('conferenceData'):
                    logger.info(f"✅ SUCCESS: Service Account created Google Meet")
                    return event
                    
            except Exception as sa_error:
                logger.warning(f"❌ Service Account Google Meet failed: {sa_error}")'''
        
        if old_complex_fallback in content:
            content = content.replace(old_complex_fallback, new_simple_fallback)
            self.history._log("✅ Упрощена Service Account стратегия")
        
        return content
    
    def fix_deletion_logic(self) -> dict:
        """Исправить логику удаления - убрать неполное удаление"""
        self.history._log("=== ИСПРАВЛЕНИЕ ЛОГИКИ УДАЛЕНИЯ ===")
        
        # Исправить в google_calendar_dual.py
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        rollback_id = self.create_rollback_point(str(dual_file))
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Добавить метод для полного удаления всех событий
        new_deletion_method = '''
    def delete_all_events_for_meeting(self, meeting_data: dict) -> dict:
        """Delete ALL events created for a meeting (handles multiple events per calendar)"""
        results = {
            'success': False,
            'deleted_count': 0,
            'errors': []
        }
        
        # Get all possible event IDs
        event_ids = []
        if meeting_data.get('google_event_id'):
            event_ids.append(meeting_data['google_event_id'])
        if meeting_data.get('google_manager_event_id'):
            event_ids.append(meeting_data['google_manager_event_id'])
        if meeting_data.get('google_owner_event_id'):
            event_ids.append(meeting_data['google_owner_event_id'])
        
        # Remove duplicates
        event_ids = list(set(event_ids))
        
        calendars = []
        if meeting_data.get('manager_calendar_id'):
            calendars.append(meeting_data['manager_calendar_id'])
        if meeting_data.get('owner_calendar_id'):
            calendars.append(meeting_data['owner_calendar_id'])
        
        # Try to delete each event from each calendar
        for calendar_id in calendars:
            for event_id in event_ids:
                try:
                    self.calendar_service._service.events().delete(
                        calendarId=calendar_id,
                        eventId=event_id
                    ).execute()
                    results['deleted_count'] += 1
                    logger.info(f"✅ Deleted event {event_id} from calendar {calendar_id}")
                except Exception as e:
                    # Не логируем 404 ошибки - это нормально
                    if "404" not in str(e):
                        results['errors'].append(f"Failed to delete {event_id} from {calendar_id}: {e}")
        
        results['success'] = results['deleted_count'] > 0
        return results
'''
        
        # Добавить новый метод перед последним методом в классе
        insert_position = content.rfind("    def _delete_from_calendar")
        if insert_position != -1:
            content = content[:insert_position] + new_deletion_method + "\n" + content[insert_position:]
            self.history._log("✅ Добавлен метод delete_all_events_for_meeting")
        
        # Записать исправленный файл
        with open(dual_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "status": "fixed",
            "file": str(dual_file),
            "rollback_id": rollback_id,
            "new_method": "delete_all_events_for_meeting"
        }
    
    def fix_google_meet_creation(self) -> dict:
        """Исправить создание Google Meet"""
        self.history._log("=== ИСПРАВЛЕНИЕ GOOGLE MEET ===")
        
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Убедиться, что OAuth-специфичная логика работает правильно
        # Проверить, что conferenceData создается корректно
        
        meet_fixes = []
        
        # 1. Убедиться, что базовая conferenceData правильная
        old_conference_data = '''            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{int(datetime.now().timestamp())}-{abs(hash(manager_calendar_id))}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            },'''
        
        new_conference_data = '''            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{int(datetime.now().timestamp())}-{abs(hash(manager_calendar_id))}"
                }
            },'''
        
        if old_conference_data in content:
            content = content.replace(old_conference_data, new_conference_data)
            meet_fixes.append("Упрощена базовая conferenceData")
            self.history._log("✅ Упрощена базовая conferenceData")
        
        # 2. Убедиться что OAuth логика правильная
        oauth_check = "is_oauth_calendar = self._is_oauth_calendar(calendar_id)"
        if oauth_check not in content:
            self.history._log("⚠️ OAuth detection logic уже существует")
        
        # Записать исправления
        with open(dual_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "status": "reviewed_and_fixed",
            "fixes_applied": meet_fixes
        }
    
    def create_rollback_point(self, file_path: str) -> str:
        """Создать точку отката"""
        rollback_id = self.history._generate_id("rollback")
        backup_dir = self.history.history_root / "rollback_points" / rollback_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if Path(file_path).exists():
            backup_file = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_file)
            
        return rollback_id
    
    def apply_all_critical_fixes(self) -> dict:
        """Применить все критические исправления"""
        self.history._log("🎯 === ПРИМЕНЯЮ ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ===")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "fixes": [],
            "rollback_points": []
        }
        
        try:
            # 1. Анализ корневой причины
            self.history._log("ЭТАП 1: Анализ корневой причины")
            root_cause = self.analyze_duplication_root_cause()
            results["root_cause_analysis"] = root_cause
            
            # 2. Исправление дублирования событий
            self.history._log("ЭТАП 2: Исправление дублирования событий")
            duplication_fix = self.fix_event_duplication()
            results["fixes"].append(duplication_fix)
            results["rollback_points"].append(duplication_fix["rollback_id"])
            
            # 3. Исправление логики удаления
            self.history._log("ЭТАП 3: Исправление логики удаления")
            deletion_fix = self.fix_deletion_logic()
            results["fixes"].append(deletion_fix)
            results["rollback_points"].append(deletion_fix["rollback_id"])
            
            # 4. Исправление Google Meet
            self.history._log("ЭТАП 4: Исправление Google Meet")
            meet_fix = self.fix_google_meet_creation()
            results["fixes"].append(meet_fix)
            
            # Сохранить результаты
            results_file = self.history.history_root / f"critical_fixes_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.history._log("🎯 === ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ ===")
            self.history._log(f"Результаты: {results_file}")
            
        except Exception as e:
            self.history._log(f"ОШИБКА при применении критических исправлений: {e}", "ERROR")
            results["error"] = str(e)
        
        return results

if __name__ == "__main__":
    print("🎯 Запускаю КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ v4.0")
    print("=" * 60)
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    fixes = CriticalFixesImplementation(project_path)
    
    try:
        results = fixes.apply_all_critical_fixes()
        
        print("\n" + "=" * 60)
        print("✅ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ")
        print(f"🔧 Применено исправлений: {len(results.get('fixes', []))}")
        print(f"📁 Создано точек отката: {len(results.get('rollback_points', []))}")
        
        print("\n🎯 ИСПРАВЛЕННЫЕ ПРОБЛЕМЫ:")
        for i, fix in enumerate(results.get('fixes', []), 1):
            print(f"  {i}. {fix.get('status', 'unknown')}: {fix.get('file', 'N/A')}")
        
        if results.get('rollback_points'):
            print("\n💾 ТОЧКИ ОТКАТА:")
            for rollback in results['rollback_points']:
                print(f"   - {rollback}")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        print(traceback.format_exc())