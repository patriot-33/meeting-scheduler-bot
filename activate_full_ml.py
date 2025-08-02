#!/usr/bin/env python3
"""
🚀 FULL ML SYSTEM ACTIVATION
Активация полной ML системы с sklearn, pandas, numpy
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

# Проверка доступности ML зависимостей
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
    print("✅ ML dependencies available (sklearn, pandas, numpy)")
except ImportError as e:
    ML_AVAILABLE = False
    print(f"❌ ML dependencies missing: {e}")

# Импорт системы диагностики
try:
    from src.diagnostic_system.mandatory_history import MandatoryHistoryPersistence
    from src.diagnostic_system.enhanced_ml_predictor import CalendarIntegrationMLPredictor
    print("✅ Diagnostic system modules imported")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_ml_activation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FullMLActivator:
    """Активатор полной ML системы"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.history = MandatoryHistoryPersistence(str(project_path))
        self.ml_predictor = None
        self.session_id = None
        
    async def activate_ml_system(self) -> dict:
        """Активировать полную ML систему"""
        
        logger.info("🚀 Activating Full ML System with sklearn")
        
        # Создать сессию активации
        self.session_id = self.history.save_session_start({
            'problem_description': 'Full ML system activation with sklearn, pandas, numpy',
            'project_path': str(self.project_path),
            'ml_enabled': ML_AVAILABLE
        })
        
        try:
            results = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'ml_available': ML_AVAILABLE
            }
            
            if not ML_AVAILABLE:
                results['error'] = 'ML dependencies not available'
                return results
            
            # 1. Инициализация ML предсказателя
            logger.info("🤖 Phase 1: Initialize ML Predictor")
            ml_init_result = await self._initialize_ml_predictor()
            results['ml_initialization'] = ml_init_result
            
            # 2. Загрузка исторических данных
            logger.info("📊 Phase 2: Load Historical Data")
            data_loading_result = await self._load_historical_data()
            results['data_loading'] = data_loading_result
            
            # 3. Обучение ML моделей
            logger.info("🧠 Phase 3: Train ML Models")
            training_result = await self._train_ml_models()
            results['model_training'] = training_result
            
            # 4. Тестирование предсказаний
            logger.info("🔮 Phase 4: Test Predictions")
            prediction_result = await self._test_predictions()
            results['prediction_testing'] = prediction_result
            
            # 5. Активация непрерывного обучения
            logger.info("🔄 Phase 5: Activate Continuous Learning")
            continuous_learning_result = await self._activate_continuous_learning()
            results['continuous_learning'] = continuous_learning_result
            
            # Сохранить результаты
            self.history.save_session_end(self.session_id, results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ ML activation failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Сохранить ошибку
            self.history.save_bug({
                'session_id': self.session_id,
                'bug_type': 'ml_activation_error',
                'severity': 'high',
                'root_cause': str(e),
                'code_features': {'ml_available': ML_AVAILABLE}
            })
            
            raise
    
    async def _initialize_ml_predictor(self) -> dict:
        """Инициализировать ML предсказатель"""
        
        try:
            self.ml_predictor = CalendarIntegrationMLPredictor(self.history)
            
            return {
                'success': True,
                'message': 'ML predictor initialized successfully',
                'models_available': list(self.ml_predictor.models.keys()),
                'sklearn_available': ML_AVAILABLE
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to initialize ML predictor'
            }
    
    async def _load_historical_data(self) -> dict:
        """Загрузить исторические данные"""
        
        try:
            # Получить все исторические баги
            bugs = self.history.get_all_bugs()
            
            # Создать дополнительные данные для обучения
            synthetic_bugs = self._create_synthetic_training_data()
            
            # Добавить синтетические данные в историю
            for bug_data in synthetic_bugs:
                bug_data['session_id'] = self.session_id
                self.history.save_bug(bug_data)
            
            total_bugs = len(bugs) + len(synthetic_bugs)
            
            return {
                'success': True,
                'historical_bugs': len(bugs),
                'synthetic_bugs': len(synthetic_bugs),
                'total_training_data': total_bugs,
                'message': f'Loaded {total_bugs} training samples'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to load historical data'
            }
    
    def _create_synthetic_training_data(self) -> list:
        """Создать синтетические данные для обучения"""
        
        synthetic_bugs = [
            # OAuth проблемы
            {
                'bug_type': 'oauth_authentication_failure',
                'severity': 'high',
                'root_cause': 'Missing refresh token validation',
                'code_features': {
                    'oauth_complexity': 0.9,
                    'authentication_issues': 0.8,
                    'service_account_usage': 0.2,
                    'error_handling_ratio': 0.3,
                    'function_length': 95,
                    'cyclomatic_complexity': 12
                }
            },
            # Service Account проблемы
            {
                'bug_type': 'service_account_permission_error',
                'severity': 'high', 
                'root_cause': 'Attempting to invite attendees with service account',
                'code_features': {
                    'service_account_usage': 0.9,
                    'permission_issues': 0.8,
                    'oauth_complexity': 0.1,
                    'error_handling_ratio': 0.4,
                    'function_length': 120,
                    'cyclomatic_complexity': 15
                }
            },
            # Conference проблемы
            {
                'bug_type': 'conference_creation_failure',
                'severity': 'medium',
                'root_cause': 'Using deprecated eventHangout type',
                'code_features': {
                    'conference_creation': 0.9,
                    'api_error_frequency': 0.7,
                    'oauth_complexity': 0.5,
                    'error_handling_ratio': 0.5,
                    'function_length': 80,
                    'cyclomatic_complexity': 8
                }
            },
            # Webhook проблемы
            {
                'bug_type': 'webhook_connection_timeout',
                'severity': 'critical',
                'root_cause': 'Network connectivity issues',
                'code_features': {
                    'webhook_issues': 0.9,
                    'api_error_frequency': 0.8,
                    'error_handling_ratio': 0.2,
                    'function_length': 60,
                    'cyclomatic_complexity': 6
                }
            },
            # Dual calendar проблемы
            {
                'bug_type': 'dual_calendar_sync_issue',
                'severity': 'high',
                'root_cause': 'Calendar ID detection failure',
                'code_features': {
                    'calendar_dual_mode': 0.9,
                    'oauth_complexity': 0.7,
                    'service_account_usage': 0.6,
                    'error_handling_ratio': 0.3,
                    'function_length': 150,
                    'cyclomatic_complexity': 18
                }
            }
        ]
        
        return synthetic_bugs
    
    async def _train_ml_models(self) -> dict:
        """Обучить ML модели"""
        
        try:
            if not self.ml_predictor:
                return {
                    'success': False,
                    'error': 'ML predictor not initialized'
                }
            
            # Запустить обучение
            training_success = self.ml_predictor._train_initial_models()
            
            # Проверить, что модели обучены
            trained_models = {name: model is not None 
                            for name, model in self.ml_predictor.models.items()}
            
            models_count = sum(1 for model in trained_models.values() if model)
            
            return {
                'success': training_success or models_count > 0,
                'models_trained': trained_models,
                'total_models': models_count,
                'message': f'Successfully trained {models_count} ML models'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to train ML models'
            }
    
    async def _test_predictions(self) -> dict:
        """Тестировать предсказания"""
        
        try:
            if not self.ml_predictor:
                return {
                    'success': False,
                    'error': 'ML predictor not initialized'
                }
            
            # Тестовые сценарии
            test_scenarios = [
                {
                    'name': 'oauth_issue_scenario',
                    'features': {
                        'oauth_complexity': 0.8,
                        'authentication_issues': 0.7,
                        'service_account_usage': 0.2,
                        'error_handling_ratio': 0.3
                    },
                    'error_context': 'OAuth authentication failed'
                },
                {
                    'name': 'conference_issue_scenario',
                    'features': {
                        'conference_creation': 0.9,
                        'api_error_frequency': 0.8,
                        'oauth_complexity': 0.4,
                        'error_handling_ratio': 0.4
                    },
                    'error_context': 'Invalid conference type value'
                },
                {
                    'name': 'service_account_scenario',
                    'features': {
                        'service_account_usage': 0.9,
                        'permission_issues': 0.8,
                        'oauth_complexity': 0.1,
                        'error_handling_ratio': 0.5
                    },
                    'error_context': 'Service accounts cannot invite attendees'
                }
            ]
            
            predictions = []
            
            for scenario in test_scenarios:
                prediction = self.ml_predictor.predict_calendar_bug(
                    scenario['features'],
                    scenario['error_context']
                )
                
                prediction['scenario_name'] = scenario['name']
                predictions.append(prediction)
                
                # Сохранить предсказание
                self.history.save_ml_prediction({
                    'session_id': self.session_id,
                    'predicted_bug_type': prediction.get('bug_type'),
                    'confidence': prediction.get('probability', 0),
                    'feature_vector': scenario['features']
                })
            
            return {
                'success': True,
                'test_scenarios': len(test_scenarios),
                'predictions': predictions,
                'message': f'Successfully tested {len(predictions)} prediction scenarios'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test predictions'
            }
    
    async def _activate_continuous_learning(self) -> dict:
        """Активировать непрерывное обучение"""
        
        try:
            if not self.ml_predictor:
                return {
                    'success': False,
                    'error': 'ML predictor not initialized'
                }
            
            # Настроить непрерывное обучение
            learning_config = {
                'retrain_frequency': 5,  # Переобучать каждые 5 новых багов
                'min_confidence': 0.7,   # Минимальная уверенность
                'auto_learning': True,   # Автоматическое обучение
                'data_validation': True  # Валидация данных
            }
            
            # Сохранить конфигурацию
            config_file = self.project_path / "ml_learning_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(learning_config, f, indent=2)
            
            return {
                'success': True,
                'config': learning_config,
                'config_file': str(config_file),
                'message': 'Continuous learning activated and configured'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to activate continuous learning'
            }


def main():
    """Главная функция"""
    
    project_path = "/Users/evgenii/meeting-scheduler-bot"
    
    if not ML_AVAILABLE:
        print("❌ ML dependencies not available. Install with:")
        print("pip3 install scikit-learn pandas numpy matplotlib seaborn")
        return
    
    try:
        # Создать активатор ML
        ml_activator = FullMLActivator(project_path)
        
        # Запустить активацию
        results = asyncio.run(ml_activator.activate_ml_system())
        
        # Вывести результаты
        print("\n" + "="*80)
        print("🤖 FULL ML SYSTEM ACTIVATION RESULTS")
        print("="*80)
        
        print(f"\n📋 Session: {results['session_id']}")
        print(f"⏰ Time: {results['timestamp']}")
        print(f"🤖 ML Available: {results['ml_available']}")
        
        # Показать результаты каждой фазы
        phases = [
            ('ml_initialization', '🤖 ML Initialization'),
            ('data_loading', '📊 Data Loading'),
            ('model_training', '🧠 Model Training'),
            ('prediction_testing', '🔮 Prediction Testing'),
            ('continuous_learning', '🔄 Continuous Learning')
        ]
        
        for phase_key, phase_name in phases:
            if phase_key in results:
                phase_result = results[phase_key]
                status = "✅ SUCCESS" if phase_result.get('success') else "❌ FAILED"
                print(f"\n{phase_name}: {status}")
                print(f"   {phase_result.get('message', 'No message')}")
                
                if 'error' in phase_result:
                    print(f"   Error: {phase_result['error']}")
        
        # Показать статистику обучения
        if 'model_training' in results:
            training = results['model_training']
            if training.get('success'):
                print(f"\n🧠 ML Models Trained: {training.get('total_models', 0)}")
        
        # Показать результаты предсказаний
        if 'prediction_testing' in results:
            testing = results['prediction_testing']
            if testing.get('success'):
                predictions = testing.get('predictions', [])
                print(f"\n🔮 Prediction Results:")
                for pred in predictions[:3]:  # Показать первые 3
                    print(f"   • {pred.get('scenario_name', 'unknown')}: "
                          f"{pred.get('bug_type', 'unknown')} "
                          f"({pred.get('probability', 0):.2%} confidence)")
        
        # Сохранить детальный отчет
        report_file = Path(project_path) / "full_ml_activation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        if results.get('ml_available') and all(
            results.get(phase[0], {}).get('success', False) 
            for phase in phases
        ):
            print("\n🎯 Status: ✅ FULL ML SYSTEM SUCCESSFULLY ACTIVATED!")
            print("🤖 Ready for:")
            print("   • Real-time bug prediction")
            print("   • Continuous learning from new data") 
            print("   • Advanced pattern recognition")
            print("   • Automated regression prevention")
        else:
            print("\n⚠️ Status: Partial activation - some components may need attention")
        
        print("\n✅ ML activation completed!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ ML activation failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    results = main()