#!/usr/bin/env python3
"""
🛠️ SAFE REPAIR ENGINE v4.0 - ТОЧНЫЕ ИСПРАВЛЕНИЯ
Безопасное исправление обнаруженных критических проблем с ОБЯЗАТЕЛЬНЫМ сохранением истории
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from diagnostic_system_v4 import MandatoryHistoryPersistence
import re
import ast

class SafeRepairEngine:
    """Движок безопасного исправления с полным контролем"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history = MandatoryHistoryPersistence(project_root)
        self.rollback_points = []
        
    def create_rollback_point(self, file_path: str) -> str:
        """Создать точку отката для файла"""
        rollback_id = self.history._generate_id("rollback")
        
        # Создать папку для бэкапов
        backup_dir = self.history.history_root / "rollback_points" / rollback_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Скопировать файл
        if Path(file_path).exists():
            backup_file = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_file)
            
            rollback_info = {
                "rollback_id": rollback_id,
                "original_file": file_path,
                "backup_file": str(backup_file),
                "timestamp": datetime.now().isoformat()
            }
            
            # Сохранить информацию о точке отката
            with open(backup_dir / "rollback_info.json", 'w') as f:
                json.dump(rollback_info, f, indent=2)
            
            self.history._log(f"Создана точка отката: {rollback_id} для {file_path}")
            return rollback_id
        
        return None
    
    def analyze_google_calendar_dual_issues(self) -> dict:
        """Детальный анализ проблем в google_calendar_dual.py"""
        file_path = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найти все вызовы events().insert
        insert_calls = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'events().insert' in line:
                insert_calls.append({
                    "line_number": i,
                    "content": line.strip(),
                    "context": self.get_line_context(lines, i-1, 3)
                })
        
        analysis = {
            "file": str(file_path),
            "total_insert_calls": len(insert_calls),
            "insert_calls": insert_calls,
            "issues_found": []
        }
        
        # Определить проблемы
        if len(insert_calls) > 3:  # Ожидаем максимум 3: основной + 2 fallback
            analysis["issues_found"].append({
                "type": "excessive_insert_calls",
                "description": f"Найдено {len(insert_calls)} вызовов events().insert, ожидалось не более 3",
                "severity": "critical"
            })
        
        # Проверить на дублирование в одном методе
        method_calls = self.group_calls_by_method(insert_calls, lines)
        for method, calls in method_calls.items():
            if len(calls) > 1:
                analysis["issues_found"].append({
                    "type": "duplicate_calls_in_method",
                    "method": method,
                    "calls": len(calls),
                    "severity": "critical"
                })
        
        return analysis
    
    def get_line_context(self, lines: list, line_index: int, context_lines: int = 3) -> dict:
        """Получить контекст вокруг строки"""
        start = max(0, line_index - context_lines)
        end = min(len(lines), line_index + context_lines + 1)
        
        return {
            "before": lines[start:line_index],
            "target": lines[line_index] if line_index < len(lines) else "",
            "after": lines[line_index+1:end]
        }
    
    def group_calls_by_method(self, insert_calls: list, lines: list) -> dict:
        """Сгруппировать вызовы по методам"""
        methods = {}
        
        for call in insert_calls:
            # Найти имя метода
            method_name = self.find_method_name(lines, call["line_number"] - 1)
            if method_name not in methods:
                methods[method_name] = []
            methods[method_name].append(call)
        
        return methods
    
    def find_method_name(self, lines: list, line_index: int) -> str:
        """Найти имя метода, содержащего строку"""
        # Идем назад от строки до def
        for i in range(line_index, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                # Извлечь имя метода
                match = re.match(r'def\s+(\w+)', line)
                if match:
                    return match.group(1)
        return "unknown"
    
    def fix_google_calendar_dual_duplication(self) -> dict:
        """Исправить дублирование в google_calendar_dual.py"""
        file_path = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        # Создать точку отката
        rollback_id = self.create_rollback_point(str(file_path))
        
        # Анализировать проблемы
        analysis = self.analyze_google_calendar_dual_issues()
        
        if not analysis.get("issues_found"):
            return {"status": "no_issues_found", "analysis": analysis}
        
        # Прочитать файл
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ИСПРАВЛЕНИЕ: Убрать дублирование в _create_event_with_fallback
        fixed_content = self.fix_create_event_with_fallback_method(content)
        
        # Записать исправленный файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        # Сохранить информацию об исправлении
        fix_info = {
            "file": str(file_path),
            "rollback_id": rollback_id,
            "issues_fixed": analysis["issues_found"],
            "timestamp": datetime.now().isoformat(),
            "changes": "Removed duplicate events().insert calls in fallback strategies"
        }
        
        self.history._log(f"Исправлен файл: {file_path}")
        
        return {
            "status": "fixed",
            "fix_info": fix_info,
            "rollback_id": rollback_id
        }
    
    def fix_create_event_with_fallback_method(self, content: str) -> str:
        """Исправить метод _create_event_with_fallback"""
        self.history._log("Исправляю метод _create_event_with_fallback")
        
        # Найти и заменить проблемный код
        # Заменить избыточные вызовы в альтернативных стратегиях
        
        # Исправление 1: В Strategy 3 убрать лишние вызовы
        old_strategy3 = '''        # Strategy 3: Universal alternative conference data formats (both OAuth and Service Account)
        if has_conference:
            logger.info("🔄 Trying universal Google Meet formats...")
            
            # Choose formats based on calendar type
            if is_oauth_calendar:
                alternative_formats = [
                    # OAuth Format 1: Minimal request without conferenceSolutionKey
                    {
                        'conferenceData': {
                            'createRequest': {
                                'requestId': f"oauth-min-{int(datetime.now().timestamp())}"
                            }
                        }
                    }
                ]
            else:
                alternative_formats = [
                    # Service Account Format 1: Explicit hangouts meet request  
                    {
                        'conferenceData': {
                            'createRequest': {
                                'requestId': f"meet-hang-{int(datetime.now().timestamp())}",
                                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                            }
                        }
                    },
                    # Service Account Format 2: Conference with entry points
                    {
                        'conferenceData': {
                            'conferenceSolution': {
                                'key': {'type': 'hangoutsMeet'},
                                'name': 'Google Meet'
                            },
                            'createRequest': {
                                'requestId': f"meet-alt-{int(datetime.now().timestamp())}"
                            }
                        }
                    }
                ]
            
            for i, alt_format in enumerate(alternative_formats):
                try:
                    alt_event_data = event_data.copy()
                    alt_event_data.update(alt_format)
                    
                    logger.info(f"🔄 Trying {calendar_type} alternative format {i+1}/{len(alternative_formats)}")
                    
                    # OAuth calendars prefer no conferenceDataVersion
                    if is_oauth_calendar:
                        event = self.calendar_service._service.events().insert(
                            calendarId=calendar_id,
                            body=alt_event_data
                        ).execute()
                    else:
                        event = self.calendar_service._service.events().insert(
                            calendarId=calendar_id,
                            body=alt_event_data,
                            conferenceDataVersion=1
                        ).execute()
                    
                    # Verify Google Meet was created
                    if event.get('conferenceData') and event.get('conferenceData').get('conferenceId'):
                        logger.info(f"✅ SUCCESS: Alternative format {i+1} created Google Meet!")
                        return event
                    else:
                        logger.warning(f"⚠️ Alternative format {i+1} created event but no Google Meet")
                        
                except Exception as alt_error:
                    logger.warning(f"❌ Alternative format {i+1} failed: {alt_error}")
                    continue'''
        
        new_strategy3 = '''        # Strategy 3: Final attempt with basic event (only if all conference creation failed)
        logger.info("🔄 All Google Meet creation attempts failed, trying basic event...")'''
        
        # Заменить избыточную стратегию
        if old_strategy3 in content:
            content = content.replace(old_strategy3, new_strategy3)
            self.history._log("Удалена избыточная Strategy 3 с дублированием events().insert")
        
        # Исправление 2: Убрать дублирование в Strategy 4 и 5
        old_strategy4 = '''        # Strategy 4: Handle attendee errors but keep trying Google Meet
        if has_attendees:
            logger.info("🔄 Retrying without attendees but keeping Google Meet...")
            try:
                no_attendees_data = event_data.copy()
                no_attendees_data.pop('attendees', None)
                
                # Apply calendar-specific approach for no attendees strategy
                if is_oauth_calendar:
                    event = self.calendar_service._service.events().insert(
                        calendarId=calendar_id,
                        body=no_attendees_data
                    ).execute()
                else:
                    event = self.calendar_service._service.events().insert(
                        calendarId=calendar_id,
                        body=no_attendees_data,
                        conferenceDataVersion=1
                    ).execute()
                
                if event.get('conferenceData'):
                    logger.info(f"✅ SUCCESS: Created Google Meet without attendees in {calendar_type}'s calendar")
                    return event
                else:
                    logger.warning(f"⚠️ Event created without attendees but no Google Meet")
                    
            except Exception as no_attendees_error:
                logger.warning(f"❌ No attendees attempt failed: {no_attendees_error}")'''
        
        new_strategy4 = '''        # Strategy 4: Final fallback - basic event without Google Meet and attendees'''
        
        if old_strategy4 in content:
            content = content.replace(old_strategy4, new_strategy4)
            self.history._log("Упрощена Strategy 4 - убрано дублирование")
        
        return content
    
    def fix_meeting_service_duplication(self) -> dict:
        """Исправить дублирование в meeting_service.py"""
        file_path = self.project_root / "src" / "services" / "meeting_service.py"
        
        # Создать точку отката
        rollback_id = self.create_rollback_point(str(file_path))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Анализировать и исправить дублирование логики создания
        lines = content.split('\n')
        creation_issues = []
        
        # Найти дублирование в create_meeting
        for i, line in enumerate(lines):
            if 'dual_calendar_creator.create_meeting_in_both_calendars' in line:
                creation_issues.append(i + 1)
        
        if len(creation_issues) > 1:
            self.history._log(f"Найдено {len(creation_issues)} вызовов dual_calendar_creator в meeting_service.py")
            
            # ИСПРАВЛЕНИЕ: Оставить только основной вызов, убрать fallback дублирование
            fixed_content = self.remove_fallback_duplication_in_meeting_service(content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            fix_info = {
                "file": str(file_path),
                "rollback_id": rollback_id,
                "issues_fixed": f"Removed {len(creation_issues)-1} duplicate creation calls",
                "timestamp": datetime.now().isoformat()
            }
            
            self.history._log(f"Исправлен meeting_service.py: убрано дублирование создания")
            return {"status": "fixed", "fix_info": fix_info}
        
        return {"status": "no_issues_found"}
    
    def remove_fallback_duplication_in_meeting_service(self, content: str) -> str:
        """Убрать дублирование fallback логики в meeting_service"""
        
        # Найти и заменить дублирующийся fallback блок
        fallback_pattern = r'''# If manager's calendar failed, try owner's calendar as fallback.*?else:\s*raise calendar_error'''
        
        # Заменить на простое перебрасывание ошибки
        replacement = '''# Propagate the error - no fallback duplication
                        raise calendar_error'''
        
        # Убрать избыточный fallback блок в create_meeting
        fixed_content = re.sub(fallback_pattern, replacement, content, flags=re.DOTALL)
        
        return fixed_content
    
    def consolidate_calendar_services(self) -> dict:
        """Консолидировать календарные сервисы"""
        self.history._log("Консолидирую календарные сервисы")
        
        # Анализировать использование google_calendar.py и google_calendar_dual.py
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        single_file = self.project_root / "src" / "services" / "google_calendar.py"
        
        consolidation_plan = {
            "primary_service": "google_calendar_dual.py",
            "deprecated_service": "google_calendar.py", 
            "consolidation_steps": [
                "Migrate all functionality to DualCalendarCreator",
                "Update imports across the codebase",
                "Remove deprecated single calendar service"
            ]
        }
        
        # Сохранить план консолидации
        plan_file = self.history.history_root / "consolidation_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(consolidation_plan, f, indent=2)
        
        return consolidation_plan
    
    def apply_all_fixes(self) -> dict:
        """Применить все исправления последовательно"""
        self.history._log("=== НАЧИНАЮ ПРИМЕНЕНИЕ ВСЕХ ИСПРАВЛЕНИЙ ===")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": [],
            "rollback_points": [],
            "errors": []
        }
        
        try:
            # 1. Исправить google_calendar_dual.py
            self.history._log("ИСПРАВЛЕНИЕ 1: google_calendar_dual.py")
            dual_fix = self.fix_google_calendar_dual_duplication()
            results["fixes_applied"].append(dual_fix)
            if dual_fix.get("rollback_id"):
                results["rollback_points"].append(dual_fix["rollback_id"])
            
            # 2. Исправить meeting_service.py
            self.history._log("ИСПРАВЛЕНИЕ 2: meeting_service.py")
            meeting_fix = self.fix_meeting_service_duplication()
            results["fixes_applied"].append(meeting_fix)
            if meeting_fix.get("fix_info", {}).get("rollback_id"):
                results["rollback_points"].append(meeting_fix["fix_info"]["rollback_id"])
            
            # 3. Консолидировать сервисы
            self.history._log("ПЛАНИРОВАНИЕ 3: Консолидация сервисов")
            consolidation = self.consolidate_calendar_services()
            results["consolidation_plan"] = consolidation
            
            # Сохранить результаты
            results_file = self.history.history_root / f"repair_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.history._log("=== ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО ===")
            self.history._log(f"Результаты сохранены: {results_file}")
            
        except Exception as e:
            error_info = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results["errors"].append(error_info)
            self.history._log(f"ОШИБКА при применении исправлений: {e}", "ERROR")
        
        return results

if __name__ == "__main__":
    print("🛠️ Запускаю SAFE REPAIR ENGINE v4.0")
    print("=" * 60)
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    repair_engine = SafeRepairEngine(project_path)
    
    try:
        # Применить все исправления
        results = repair_engine.apply_all_fixes()
        
        print("\n" + "=" * 60)
        print("✅ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ")
        print(f"🔧 Применено исправлений: {len(results['fixes_applied'])}")
        print(f"📁 Создано точек отката: {len(results['rollback_points'])}")
        
        if results.get("errors"):
            print(f"❌ Ошибок: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"   - {error['error']}")
        
        print("\n💾 ТОЧКИ ОТКАТА:")
        for rollback_id in results["rollback_points"]:
            print(f"   - {rollback_id}")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        print(traceback.format_exc())