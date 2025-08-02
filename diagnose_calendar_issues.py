#!/usr/bin/env python3
"""
🛡️ HOLISTIC CALENDAR INTEGRATION DIAGNOSTIC SYSTEM v4.0
Полная диагностика и исправление проблем календарной интеграции с ML обучением
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback
import json

# Добавляем путь к модулям проекта
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from diagnostic_system import create_calendar_ml_system, MandatoryHistoryPersistence
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying direct import...")
    from src.diagnostic_system.mandatory_history import MandatoryHistoryPersistence
    from src.diagnostic_system.enhanced_ml_predictor import CalendarIntegrationMLPredictor

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

class CalendarDiagnosticEngine:
    """Движок для диагностики календарных проблем"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.history = MandatoryHistoryPersistence(str(project_path))
        self.ml_predictor = CalendarIntegrationMLPredictor(self.history)
        self.session_id = None
        
    async def run_full_diagnosis(self, problem_description: str) -> dict:
        """Запустить полную диагностику календарных проблем"""
        
        logger.info("🚀 Starting HOLISTIC CALENDAR DIAGNOSTIC SYSTEM v4.0")
        
        # Создать сессию диагностики
        self.session_id = self.history.save_session_start({
            'problem_description': problem_description,
            'project_path': str(self.project_path),
            'diagnostic_version': '4.0'
        })
        
        try:
            results = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'problem_description': problem_description
            }
            
            # 1. Анализ кода календарной интеграции
            logger.info("🔍 Phase 1: Code Analysis")
            code_analysis = await self._analyze_calendar_code()
            results['code_analysis'] = code_analysis
            
            # 2. Анализ логов ошибок
            logger.info("📋 Phase 2: Error Log Analysis")
            log_analysis = await self._analyze_error_logs()
            results['log_analysis'] = log_analysis
            
            # 3. ML предсказание проблем
            logger.info("🤖 Phase 3: ML Prediction")
            ml_prediction = await self._run_ml_prediction(code_analysis, log_analysis)
            results['ml_prediction'] = ml_prediction
            
            # 4. Генерация исправлений
            logger.info("🔧 Phase 4: Fix Generation")
            fixes = await self._generate_fixes(ml_prediction)
            results['suggested_fixes'] = fixes
            
            # 5. Создание плана действий
            logger.info("📋 Phase 5: Action Plan")
            action_plan = await self._create_action_plan(results)
            results['action_plan'] = action_plan
            
            # Сохранить результаты
            self.history.save_session_end(self.session_id, results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Diagnostic failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Сохранить ошибку
            self.history.save_bug({
                'session_id': self.session_id,
                'bug_type': 'diagnostic_system_error',
                'severity': 'high',
                'root_cause': str(e),
                'code_features': {}
            })
            
            raise
    
    async def _analyze_calendar_code(self) -> dict:
        """Анализ кода календарной интеграции"""
        
        calendar_files = [
            'src/services/google_calendar_dual.py',
            'src/services/google_calendar.py', 
            'src/services/meeting_service.py',
            'src/main.py'
        ]
        
        analysis_results = {}
        
        for file_path in calendar_files:
            full_path = self.project_path / file_path
            if full_path.exists():
                logger.info(f"📄 Analyzing {file_path}")
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                
                # Извлечь признаки
                features = self.ml_predictor.extract_calendar_features(code_content)
                
                analysis_results[file_path] = {
                    'features': features,
                    'lines_of_code': len(code_content.split('\n')),
                    'complexity_score': features.get('cyclomatic_complexity', 0),
                    'oauth_complexity': features.get('oauth_complexity', 0),
                    'service_account_usage': features.get('service_account_usage', 0),
                    'error_handling_ratio': features.get('error_handling_ratio', 0)
                }
                
                # Сохранить для ML обучения
                if features.get('api_error_frequency', 0) > 0.5:
                    self.history.save_bug({
                        'session_id': self.session_id,
                        'bug_type': 'high_api_error_frequency',
                        'severity': 'medium',
                        'root_cause': 'High frequency of API errors detected in code',
                        'code_features': features
                    })
        
        return analysis_results
    
    async def _analyze_error_logs(self) -> dict:
        """Анализ логов ошибок"""
        
        # Анализ известных ошибок из логов Render
        render_errors = """
        Invalid conference type value
        Service accounts cannot invite attendees
        events not created in calendars
        webhook connection timeout
        """
        
        # Извлечь признаки из логов
        log_features = self.ml_predictor.extract_calendar_features("", render_errors)
        
        # Классифицировать ошибки
        error_categories = {
            'oauth_issues': log_features.get('authentication_issues', 0),
            'service_account_issues': log_features.get('permission_issues', 0), 
            'conference_issues': 1.0 if 'Invalid conference type' in render_errors else 0.0,
            'webhook_issues': log_features.get('webhook_issues', 0),
            'api_errors': log_features.get('api_error_frequency', 0)
        }
        
        # Сохранить критические ошибки
        for error_type, severity_score in error_categories.items():
            if severity_score > 0.5:
                self.history.save_bug({
                    'session_id': self.session_id,
                    'bug_type': error_type,
                    'severity': 'high' if severity_score > 0.8 else 'medium',
                    'root_cause': f'Detected from error logs: {error_type}',
                    'code_features': {'error_severity': severity_score}
                })
        
        return {
            'error_categories': error_categories,
            'log_features': log_features,
            'critical_errors': [k for k, v in error_categories.items() if v > 0.5]
        }
    
    async def _run_ml_prediction(self, code_analysis: dict, log_analysis: dict) -> dict:
        """Запустить ML предсказание"""
        
        # Агрегировать признаки со всех файлов
        aggregated_features = {}
        
        for file_data in code_analysis.values():
            features = file_data.get('features', {})
            for key, value in features.items():
                if key in aggregated_features:
                    aggregated_features[key] = max(aggregated_features[key], value)
                else:
                    aggregated_features[key] = value
        
        # Добавить признаки из логов
        aggregated_features.update(log_analysis.get('log_features', {}))
        
        # Запустить предсказание
        prediction = self.ml_predictor.predict_calendar_bug(
            aggregated_features, 
            error_context="Invalid conference type value, Service accounts cannot invite attendees"
        )
        
        # Сохранить предсказание для обучения
        self.history.save_ml_prediction({
            'session_id': self.session_id,
            'predicted_bug_type': prediction.get('bug_type'),
            'confidence': prediction.get('probability', 0),
            'feature_vector': aggregated_features
        })
        
        logger.info(f"🤖 ML Prediction: {prediction.get('bug_type')} "
                   f"(confidence: {prediction.get('probability', 0):.2f})")
        
        return prediction
    
    async def _generate_fixes(self, ml_prediction: dict) -> dict:
        """Генерировать конкретные исправления"""
        
        bug_type = ml_prediction.get('bug_type')
        fixes = {}
        
        if bug_type == 'conference_creation_failure':
            fixes['conference_type_fix'] = {
                'file': 'src/services/google_calendar_dual.py',
                'line_range': [96, 98],
                'current_code': "'type': 'eventHangout'",
                'fixed_code': "'type': 'hangoutsMeet'",
                'description': 'Change conference type from eventHangout to hangoutsMeet',
                'confidence': 0.95
            }
        
        if bug_type == 'oauth_authentication_failure':
            fixes['oauth_detection_fix'] = {
                'file': 'src/services/google_calendar_dual.py', 
                'line_range': [292, 301],
                'description': 'Improve OAuth detection with proper refresh_token validation',
                'confidence': 0.85
            }
        
        if bug_type == 'service_account_permission_error':
            fixes['attendee_removal_fix'] = {
                'file': 'src/services/google_calendar_dual.py',
                'description': 'Remove attendee invitations for Service Account calendars',
                'confidence': 0.90
            }
        
        # Добавить универсальные улучшения
        fixes['error_handling_improvement'] = {
            'description': 'Add comprehensive error handling and logging',
            'confidence': 0.80
        }
        
        fixes['fallback_mechanisms'] = {
            'description': 'Implement fallback strategies for API failures',
            'confidence': 0.75
        }
        
        return fixes
    
    async def _create_action_plan(self, results: dict) -> dict:
        """Создать план действий"""
        
        ml_prediction = results.get('ml_prediction', {})
        fixes = results.get('suggested_fixes', {})
        
        action_plan = {
            'priority': 'high',
            'estimated_time': '2-4 hours',
            'steps': []
        }
        
        # Шаг 1: Критические исправления
        if 'conference_type_fix' in fixes:
            action_plan['steps'].append({
                'step': 1,
                'action': 'Fix conference type',
                'description': 'Change eventHangout to hangoutsMeet in google_calendar_dual.py',
                'files': ['src/services/google_calendar_dual.py'],
                'risk': 'low',
                'estimated_time': '15 minutes'
            })
        
        # Шаг 2: OAuth исправления
        if 'oauth_detection_fix' in fixes:
            action_plan['steps'].append({
                'step': 2,
                'action': 'Improve OAuth detection',
                'description': 'Fix OAuth calendar detection logic',
                'files': ['src/services/google_calendar_dual.py'],
                'risk': 'medium',
                'estimated_time': '30 minutes'
            })
        
        # Шаг 3: Тестирование
        action_plan['steps'].append({
            'step': 3,
            'action': 'Test changes',
            'description': 'Deploy and test calendar event creation',
            'risk': 'low',
            'estimated_time': '30 minutes'
        })
        
        # Шаг 4: Мониторинг
        action_plan['steps'].append({
            'step': 4,
            'action': 'Monitor results',
            'description': 'Watch logs for 24 hours to confirm fixes',
            'risk': 'low',
            'estimated_time': '24 hours (passive)'
        })
        
        return action_plan


async def main():
    """Главная функция диагностики"""
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    
    problem_description = """
    Telegram бот для планирования встреч имеет проблемы с календарной интеграцией:
    1. События не создаются в календарях Google
    2. Ошибки "Invalid conference type value" 
    3. Ошибки "Service accounts cannot invite attendees"
    4. Google Meet ссылки не создаются
    5. Проблемы с определением OAuth vs Service Account календарей
    
    Нужна полная диагностика и исправление с ML анализом.
    """
    
    try:
        # Создать диагностический движок
        diagnostic_engine = CalendarDiagnosticEngine(project_path)
        
        # Запустить диагностику
        results = await diagnostic_engine.run_full_diagnosis(problem_description)
        
        # Вывести результаты
        print("\n" + "="*80)
        print("🎯 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ")
        print("="*80)
        
        print(f"\n📋 Сессия: {results['session_id']}")
        print(f"⏰ Время: {results['timestamp']}")
        
        ml_prediction = results.get('ml_prediction', {})
        print(f"\n🤖 ML Предсказание:")
        print(f"   Тип бага: {ml_prediction.get('bug_type', 'unknown')}")
        print(f"   Вероятность: {ml_prediction.get('probability', 0):.2%}")
        print(f"   Уверенность: {ml_prediction.get('confidence', 'low')}")
        
        if 'evidence' in ml_prediction:
            print(f"   Доказательства: {ml_prediction['evidence']}")
        
        # Показать рекомендации
        if 'immediate_actions' in ml_prediction:
            print(f"\n🔧 Немедленные действия:")
            for action in ml_prediction['immediate_actions']:
                print(f"   • {action}")
        
        if 'fixes' in ml_prediction:
            print(f"\n🛠️ Исправления:")
            for fix in ml_prediction['fixes']:
                print(f"   • {fix}")
        
        # План действий
        action_plan = results.get('action_plan', {})
        if action_plan.get('steps'):
            print(f"\n📋 План действий:")
            print(f"   Приоритет: {action_plan.get('priority', 'medium')}")
            print(f"   Время: {action_plan.get('estimated_time', 'unknown')}")
            
            for step in action_plan['steps']:
                print(f"\n   Шаг {step['step']}: {step['action']}")
                print(f"      {step['description']}")
                print(f"      Время: {step.get('estimated_time', 'unknown')}")
                print(f"      Риск: {step.get('risk', 'unknown')}")
        
        # Сохранить детальный отчет
        report_file = Path(project_path) / "calendar_diagnostic_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Детальный отчет сохранен: {report_file}")
        print("\n✅ Диагностика завершена!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Diagnostic system failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    # Запустить диагностику
    results = asyncio.run(main())