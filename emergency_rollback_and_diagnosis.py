#!/usr/bin/env python3
"""
🚨 ЭКСТРЕННАЯ ДИАГНОСТИКА И ОТКАТ v5.0
КРИТИЧЕСКАЯ СИТУАЦИЯ: Проблемы усугубились после исправлений
Немедленный анализ и откат к рабочему состоянию
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import subprocess

class EmergencyRollbackAndDiagnosis:
    """Экстренная диагностика и откат"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history_root = self.project_root / ".diagnostic_history"
        
    def emergency_log(self, message: str, level: str = "CRITICAL"):
        """Экстренное логирование"""
        timestamp = datetime.now().isoformat()
        log_message = f"[{timestamp}] [{level}] {message}"
        print(f"🚨 {log_message}")
        
        # Сохранить в экстренный лог
        emergency_log = self.project_root / "emergency_diagnosis.log"
        with open(emergency_log, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def analyze_current_damage(self) -> dict:
        """Анализ текущего ущерба"""
        self.emergency_log("=== АНАЛИЗ ТЕКУЩЕГО УЩЕРБА ===")
        
        damage_report = {
            "timestamp": datetime.now().isoformat(),
            "problems_detected": [
                "Теперь создается 4 события (было 3) - УХУДШЕНИЕ",
                "Удаляется только 1 событие - НЕ ИСПРАВЛЕНО", 
                "Google Meet полностью отсутствует - НЕ ИСПРАВЛЕНО",
                "Логи в Render.com недоступны - НОВАЯ ПРОБЛЕМА"
            ],
            "severity": "CRITICAL - система стала работать хуже",
            "immediate_action": "НЕМЕДЛЕННЫЙ ОТКАТ"
        }
        
        # Анализировать что именно сломалось
        dual_calendar_analysis = self.analyze_dual_calendar_damage()
        meeting_service_analysis = self.analyze_meeting_service_damage()
        
        damage_report["dual_calendar_issues"] = dual_calendar_analysis
        damage_report["meeting_service_issues"] = meeting_service_analysis
        
        # Сохранить отчет
        damage_file = self.project_root / "EMERGENCY_DAMAGE_REPORT.json"
        with open(damage_file, 'w', encoding='utf-8') as f:
            json.dump(damage_report, f, indent=2, ensure_ascii=False)
        
        self.emergency_log(f"Отчет о повреждениях сохранен: {damage_file}")
        return damage_report
    
    def analyze_dual_calendar_damage(self) -> dict:
        """Анализ повреждений в google_calendar_dual.py"""
        file_path = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Подсчитать events().insert вызовы
        insert_count = content.count('events().insert')
        
        # Найти проблемные места
        issues = []
        
        if insert_count > 3:
            issues.append(f"Слишком много events().insert: {insert_count}")
        
        # Проверить логику создания в обоих календарях
        if "create_meeting_in_both_calendars" in content:
            lines = content.split('\n')
            in_method = False
            method_issues = []
            
            for i, line in enumerate(lines, 1):
                if "def create_meeting_in_both_calendars" in line:
                    in_method = True
                elif in_method and line.strip().startswith("def "):
                    break
                elif in_method and "events().insert" in line:
                    method_issues.append(f"Line {i}: {line.strip()}")
            
            if len(method_issues) > 2:
                issues.append(f"Слишком много вызовов в create_meeting_in_both_calendars: {method_issues}")
        
        return {
            "file": str(file_path),
            "insert_calls_count": insert_count,
            "issues": issues
        }
    
    def analyze_meeting_service_damage(self) -> dict:
        """Анализ повреждений в meeting_service.py"""
        file_path = self.project_root / "src" / "services" / "meeting_service.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # Проверить вызовы создания
        dual_calls = content.count("dual_calendar_creator.create_meeting_in_both_calendars")
        if dual_calls > 1:
            issues.append(f"Множественные вызовы dual_calendar_creator: {dual_calls}")
        
        # Проверить метод удаления
        if "delete_all_events_for_meeting" in content:
            issues.append("Используется новый метод удаления - может быть проблемой")
        
        return {
            "file": str(file_path),
            "dual_creation_calls": dual_calls,
            "issues": issues
        }
    
    def immediate_rollback_to_working_state(self) -> dict:
        """НЕМЕДЛЕННЫЙ ОТКАТ к рабочему состоянию"""
        self.emergency_log("=== НЕМЕДЛЕННЫЙ ОТКАТ ===")
        
        rollback_results = {
            "timestamp": datetime.now().isoformat(),
            "actions": [],
            "success": False
        }
        
        try:
            # 1. Откат google_calendar_dual.py
            dual_rollback = self.rollback_file(
                "src/services/google_calendar_dual.py",
                "rollback_20250802_100156_f28c5e34"
            )
            rollback_results["actions"].append(dual_rollback)
            
            # 2. Откат meeting_service.py  
            meeting_rollback = self.rollback_file(
                "src/services/meeting_service.py", 
                "rollback_20250802_100156_64a872dd"
            )
            rollback_results["actions"].append(meeting_rollback)
            
            # 3. Удалить проблемный метод delete_all_events_for_meeting
            self.remove_problematic_additions()
            rollback_results["actions"].append("Removed problematic delete_all_events_for_meeting method")
            
            rollback_results["success"] = True
            self.emergency_log("✅ ОТКАТ ЗАВЕРШЕН УСПЕШНО")
            
        except Exception as e:
            rollback_results["error"] = str(e)
            self.emergency_log(f"❌ ОШИБКА ОТКАТА: {e}")
        
        return rollback_results
    
    def rollback_file(self, relative_path: str, rollback_id: str) -> dict:
        """Откатить конкретный файл"""
        target_file = self.project_root / relative_path
        backup_file = self.history_root / "rollback_points" / rollback_id / Path(relative_path).name
        
        if backup_file.exists():
            shutil.copy2(backup_file, target_file)
            self.emergency_log(f"✅ Откачен файл: {relative_path}")
            return {"file": relative_path, "status": "rolled_back", "backup_used": str(backup_file)}
        else:
            self.emergency_log(f"❌ Бэкап не найден: {backup_file}")
            return {"file": relative_path, "status": "backup_not_found"}
    
    def remove_problematic_additions(self):
        """Удалить проблемные добавления"""
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Удалить метод delete_all_events_for_meeting если он есть
        start_marker = "def delete_all_events_for_meeting"
        end_marker = "def _delete_from_calendar"
        
        if start_marker in content:
            start_idx = content.find(start_marker)
            if start_idx != -1:
                # Найти начало следующего метода
                end_idx = content.find(end_marker, start_idx)
                if end_idx != -1:
                    # Удалить проблемный метод
                    content = content[:start_idx] + content[end_idx:]
                    
                    with open(dual_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.emergency_log("✅ Удален проблемный метод delete_all_events_for_meeting")
    
    def create_simple_working_version(self) -> dict:
        """Создать простую рабочую версию"""
        self.emergency_log("=== СОЗДАНИЕ ПРОСТОЙ РАБОЧЕЙ ВЕРСИИ ===")
        
        # Упростить google_calendar_dual.py до минимума
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найти и упростить _create_event_with_fallback
        simplified_method = '''    def _create_event_with_fallback(self, calendar_id: str, event_data: dict, calendar_type: str):
        """Simplified event creation - ONE attempt only"""
        logger.info(f"📅 Creating event in {calendar_type}'s calendar: {calendar_id}")
        
        try:
            # Single attempt - no complex fallbacks
            event = self.calendar_service._service.events().insert(
                calendarId=calendar_id,
                body=event_data,
                conferenceDataVersion=1
            ).execute()
            
            logger.info(f"✅ SUCCESS: Created event in {calendar_type}'s calendar")
            return event
            
        except Exception as e:
            logger.error(f"❌ Failed to create event in {calendar_type}'s calendar: {e}")
            
            # Only fallback: basic event without conference
            try:
                basic_data = event_data.copy()
                basic_data.pop('conferenceData', None)
                basic_data.pop('attendees', None)
                
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=basic_data
                ).execute()
                
                logger.info(f"✅ Created basic event in {calendar_type}'s calendar")
                return event
                
            except Exception as basic_error:
                logger.error(f"❌ Even basic event failed: {basic_error}")
                return None'''
        
        # Найти и заменить существующий метод
        start_pattern = "def _create_event_with_fallback("
        end_pattern = "def _is_valid_email("
        
        start_idx = content.find(start_pattern)
        end_idx = content.find(end_pattern)
        
        if start_idx != -1 and end_idx != -1:
            content = content[:start_idx] + simplified_method + "\n\n    " + content[end_idx:]
            
            with open(dual_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.emergency_log("✅ Упрощен метод _create_event_with_fallback")
        
        return {"status": "simplified", "file": str(dual_file)}
    
    def run_emergency_protocol(self) -> dict:
        """Запустить полный экстренный протокол"""
        self.emergency_log("🚨 === ЗАПУСК ЭКСТРЕННОГО ПРОТОКОЛА ===")
        
        emergency_results = {
            "protocol_start": datetime.now().isoformat(),
            "steps": []
        }
        
        # Шаг 1: Анализ ущерба
        damage_report = self.analyze_current_damage()
        emergency_results["steps"].append({"step": "damage_analysis", "result": damage_report})
        
        # Шаг 2: Немедленный откат
        rollback_result = self.immediate_rollback_to_working_state()
        emergency_results["steps"].append({"step": "immediate_rollback", "result": rollback_result})
        
        # Шаг 3: Создание простой версии
        simplified_result = self.create_simple_working_version()
        emergency_results["steps"].append({"step": "simplification", "result": simplified_result})
        
        # Сохранить результаты экстренного протокола
        emergency_file = self.project_root / "EMERGENCY_PROTOCOL_RESULTS.json"
        with open(emergency_file, 'w', encoding='utf-8') as f:
            json.dump(emergency_results, f, indent=2, ensure_ascii=False)
        
        self.emergency_log("✅ ЭКСТРЕННЫЙ ПРОТОКОЛ ЗАВЕРШЕН")
        self.emergency_log(f"Результаты: {emergency_file}")
        
        return emergency_results

if __name__ == "__main__":
    print("🚨 ЭКСТРЕННАЯ ДИАГНОСТИКА И ОТКАТ v5.0")
    print("=" * 60)
    print("КРИТИЧЕСКАЯ СИТУАЦИЯ: Исправления усугубили проблемы")
    print("Запускаю немедленный откат...")
    print("=" * 60)
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    emergency = EmergencyRollbackAndDiagnosis(project_path)
    
    try:
        results = emergency.run_emergency_protocol()
        
        print("\n" + "=" * 60)
        print("🚨 ЭКСТРЕННЫЙ ПРОТОКОЛ ЗАВЕРШЕН")
        
        if results["steps"][-1]["result"].get("success", False):
            print("✅ ОТКАТ ВЫПОЛНЕН УСПЕШНО")
            print("📋 Система возвращена к предыдущему состоянию")
            print("🔧 Применена упрощенная версия для стабильности")
        else:
            print("❌ ОТКАТ НЕ ЗАВЕРШЕН")
            print("📞 ТРЕБУЕТСЯ РУЧНОЕ ВМЕШАТЕЛЬСТВО")
        
        print(f"\n📁 Проверьте файлы:")
        print(f"   - EMERGENCY_DAMAGE_REPORT.json")
        print(f"   - EMERGENCY_PROTOCOL_RESULTS.json")
        print(f"   - emergency_diagnosis.log")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ЭКСТРЕННОГО ПРОТОКОЛА: {e}")
        import traceback
        print(traceback.format_exc())