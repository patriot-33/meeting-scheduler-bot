#!/usr/bin/env python3
"""
🔍 ROOT CAUSE ANALYZER - Поиск РЕАЛЬНОЙ причины 4 событий
Детальный анализ логики создания встреч с трассировкой каждого шага
"""

import ast
import re
from pathlib import Path

class RootCauseAnalyzer:
    """Анализатор корневой причины дублирования"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def trace_meeting_creation_flow(self) -> dict:
        """Проследить полный поток создания встречи"""
        print("🔍 === ТРАССИРОВКА ПОТОКА СОЗДАНИЯ ВСТРЕЧИ ===")
        
        flow_analysis = {
            "entry_points": [],
            "creation_calls": [],
            "potential_loops": [],
            "root_cause_hypothesis": []
        }
        
        # 1. Найти все точки входа (где вызывается создание встречи)
        entry_points = self.find_meeting_creation_entry_points()
        flow_analysis["entry_points"] = entry_points
        
        # 2. Проследить каждый create_meeting_in_both_calendars
        creation_calls = self.trace_dual_calendar_calls()
        flow_analysis["creation_calls"] = creation_calls
        
        # 3. Проанализировать DualCalendarCreator.create_meeting_in_both_calendars
        dual_analysis = self.analyze_dual_calendar_logic()
        flow_analysis["dual_calendar_logic"] = dual_analysis
        
        # 4. Найти потенциальные циклы и дублирование
        loops = self.find_potential_loops()
        flow_analysis["potential_loops"] = loops
        
        # 5. Сформулировать гипотезы корневой причины
        hypotheses = self.formulate_root_cause_hypotheses(flow_analysis)
        flow_analysis["root_cause_hypothesis"] = hypotheses
        
        return flow_analysis
    
    def find_meeting_creation_entry_points(self) -> list:
        """Найти все точки входа создания встреч"""
        entry_points = []
        
        # Поиск в handlers
        for handler_file in (self.project_root / "src" / "handlers").glob("*.py"):
            with open(handler_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if "create_meeting" in line and ("meeting_service" in line or "MeetingService" in line):
                        entry_points.append({
                            "file": str(handler_file),
                            "line": i,
                            "code": line.strip(),
                            "type": "handler_entry"
                        })
        
        return entry_points
    
    def trace_dual_calendar_calls(self) -> list:
        """Проследить все вызовы dual_calendar_creator"""
        calls = []
        
        meeting_service = self.project_root / "src" / "services" / "meeting_service.py"
        with open(meeting_service, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                if "dual_calendar_creator" in line and "create_meeting" in line:
                    calls.append({
                        "file": str(meeting_service),
                        "line": i,
                        "code": line.strip(),
                        "context": self.get_context(lines, i-1, 5)
                    })
        
        return calls
    
    def analyze_dual_calendar_logic(self) -> dict:
        """Детальный анализ логики DualCalendarCreator"""
        dual_file = self.project_root / "src" / "services" / "google_calendar_dual.py"
        
        with open(dual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = {
            "method_exists": "create_meeting_in_both_calendars" in content,
            "events_insert_calls": [],
            "calendar_creation_logic": {},
            "fallback_logic": {}
        }
        
        # Найти все events().insert вызовы
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "events().insert" in line:
                analysis["events_insert_calls"].append({
                    "line": i,
                    "code": line.strip(),
                    "in_method": self.find_containing_method(lines, i-1)
                })
        
        # Анализировать логику создания в календарях
        analysis["calendar_creation_logic"] = self.analyze_calendar_creation_logic(content)
        
        return analysis
    
    def analyze_calendar_creation_logic(self, content: str) -> dict:
        """Анализ логики создания в календарях"""
        logic = {
            "manager_calendar_creation": False,
            "owner_calendar_creation": False,
            "same_calendar_used_twice": False,
            "creation_conditions": []
        }
        
        lines = content.split('\n')
        in_create_method = False
        
        for i, line in enumerate(lines, 1):
            if "def create_meeting_in_both_calendars" in line:
                in_create_method = True
            elif in_create_method and line.strip().startswith("def "):
                break
            elif in_create_method:
                # Анализ условий создания
                if "Create in manager's calendar" in line:
                    logic["manager_calendar_creation"] = True
                    logic["creation_conditions"].append({
                        "type": "manager_creation",
                        "line": i,
                        "condition": "Always creates in manager calendar"
                    })
                
                if "Create in owner's calendar" in line:
                    logic["owner_calendar_creation"] = True
                    # Найти условие
                    condition_line = self.find_previous_if_condition(lines, i-1)
                    logic["creation_conditions"].append({
                        "type": "owner_creation",
                        "line": i,
                        "condition": condition_line if condition_line else "Unknown condition"
                    })
                
                # Проверить на использование одного календаря дважды
                if "owner_calendar_id or manager_calendar_id" in line:
                    logic["same_calendar_used_twice"] = True
                    logic["creation_conditions"].append({
                        "type": "same_calendar_reuse",
                        "line": i,
                        "condition": "owner_calendar_id or manager_calendar_id - POTENTIAL PROBLEM"
                    })
        
        return logic
    
    def find_containing_method(self, lines: list, line_idx: int) -> str:
        """Найти метод, содержащий строку"""
        for i in range(line_idx, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                match = re.match(r'def\s+(\w+)', line)
                if match:
                    return match.group(1)
        return "unknown"
    
    def find_previous_if_condition(self, lines: list, line_idx: int) -> str:
        """Найти предыдущее if условие"""
        for i in range(line_idx, max(0, line_idx-10), -1):
            line = lines[i].strip()
            if line.startswith('if ') and ':' in line:
                return line
        return None
    
    def get_context(self, lines: list, line_idx: int, context_size: int = 3) -> dict:
        """Получить контекст вокруг строки"""
        start = max(0, line_idx - context_size)
        end = min(len(lines), line_idx + context_size + 1)
        
        return {
            "before": lines[start:line_idx],
            "target": lines[line_idx] if line_idx < len(lines) else "",
            "after": lines[line_idx+1:end]
        }
    
    def find_potential_loops(self) -> list:
        """Найти потенциальные циклы создания"""
        loops = []
        
        # Проверить meeting_service.py на рекурсивные вызовы
        meeting_file = self.project_root / "src" / "services" / "meeting_service.py"
        with open(meeting_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Поиск fallback логики, которая может вызывать дублирование
        if "fallback" in content.lower():
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if "fallback" in line.lower() and "create" in line:
                    loops.append({
                        "type": "fallback_creation",
                        "file": str(meeting_file),
                        "line": i,
                        "code": line.strip()
                    })
        
        return loops
    
    def formulate_root_cause_hypotheses(self, analysis: dict) -> list:
        """Сформулировать гипотезы корневой причины"""
        hypotheses = []
        
        # Гипотеза 1: Множественные events().insert
        insert_count = len(analysis["creation_calls"])
        if insert_count > 2:
            hypotheses.append({
                "hypothesis": "Multiple events().insert calls in dual calendar logic",
                "evidence": f"Found {insert_count} events().insert calls",
                "severity": "critical",
                "likely_cause": True
            })
        
        # Гипотеза 2: Одинаковый календарь используется дважды
        dual_logic = analysis.get("dual_calendar_logic", {})
        if dual_logic.get("calendar_creation_logic", {}).get("same_calendar_used_twice"):
            hypotheses.append({
                "hypothesis": "Same calendar used twice due to 'owner_calendar_id or manager_calendar_id'",
                "evidence": "Found fallback logic that reuses same calendar",
                "severity": "critical",
                "likely_cause": True
            })
        
        # Гипотеза 3: Fallback дублирование
        if analysis["potential_loops"]:
            hypotheses.append({
                "hypothesis": "Fallback logic creates additional events",
                "evidence": f"Found {len(analysis['potential_loops'])} potential fallback loops",
                "severity": "high",
                "likely_cause": True
            })
        
        # Гипотеза 4: _create_event_with_fallback имеет внутреннее дублирование
        events_in_fallback = [call for call in dual_logic.get("events_insert_calls", []) 
                             if call["in_method"] == "_create_event_with_fallback"]
        if len(events_in_fallback) > 1:
            hypotheses.append({
                "hypothesis": "_create_event_with_fallback method has internal duplication",
                "evidence": f"Found {len(events_in_fallback)} events().insert calls in fallback method",
                "severity": "critical",
                "likely_cause": True
            })
        
        return hypotheses
    
    def generate_detailed_report(self) -> dict:
        """Создать детальный отчет"""
        print("📊 Генерирую детальный отчет...")
        
        flow_analysis = self.trace_meeting_creation_flow()
        
        report = {
            "timestamp": "2025-08-02T10:35:00",
            "problem": "4 события создается вместо 1-2",
            "analysis": flow_analysis,
            "critical_findings": [],
            "recommended_fixes": []
        }
        
        # Выделить критические находки
        for hypothesis in flow_analysis["root_cause_hypothesis"]:
            if hypothesis.get("likely_cause") and hypothesis.get("severity") == "critical":
                report["critical_findings"].append(hypothesis)
        
        # Сгенерировать рекомендации
        if report["critical_findings"]:
            for finding in report["critical_findings"]:
                if "events().insert" in finding["hypothesis"]:
                    report["recommended_fixes"].append({
                        "fix": "Reduce events().insert calls to maximum 2",
                        "priority": "immediate",
                        "target": "_create_event_with_fallback method"
                    })
                
                if "same calendar" in finding["hypothesis"]:
                    report["recommended_fixes"].append({
                        "fix": "Remove 'owner_calendar_id or manager_calendar_id' fallback",
                        "priority": "immediate", 
                        "target": "create_meeting_in_both_calendars method"
                    })
        
        return report

if __name__ == "__main__":
    print("🔍 ROOT CAUSE ANALYZER - Поиск реальной причины 4 событий")
    print("=" * 60)
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    analyzer = RootCauseAnalyzer(project_path)
    
    try:
        report = analyzer.generate_detailed_report()
        
        print(f"\n🎯 КРИТИЧЕСКИЕ НАХОДКИ: {len(report['critical_findings'])}")
        for i, finding in enumerate(report['critical_findings'], 1):
            print(f"  {i}. {finding['hypothesis']}")
            print(f"     Доказательство: {finding['evidence']}")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ: {len(report['recommended_fixes'])}")
        for i, fix in enumerate(report['recommended_fixes'], 1):
            print(f"  {i}. [{fix['priority'].upper()}] {fix['fix']}")
            print(f"     Цель: {fix['target']}")
        
        # Сохранить отчет
        report_file = Path(project_path) / "ROOT_CAUSE_ANALYSIS_REPORT.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Полный отчет сохранен: {report_file}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА АНАЛИЗА: {e}")
        import traceback
        print(traceback.format_exc())