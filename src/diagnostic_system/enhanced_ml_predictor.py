"""
Enhanced ML Bug Predictor v4.0
Специализированный ML предсказатель для календарной интеграции Telegram бота
"""
import numpy as np
import pandas as pd
import ast
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, confusion_matrix
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("⚠️ scikit-learn not available. Install with: pip install scikit-learn")

from .mandatory_history import MandatoryHistoryPersistence

logger = logging.getLogger(__name__)

class CalendarIntegrationMLPredictor:
    """ML предсказатель специально для проблем календарной интеграции"""
    
    def __init__(self, history: MandatoryHistoryPersistence):
        self.history = history
        self.models = {
            'oauth_issues': None,
            'service_account_issues': None,
            'conference_creation': None,
            'general_bugs': None
        }
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_importance = {}
        self.calendar_bug_patterns = self._load_calendar_patterns()
        
        # Инициализация с известными паттернами календарных багов
        self._initialize_with_known_patterns()
        
        if SKLEARN_AVAILABLE:
            self.load_or_train_models()
        else:
            logger.warning("🤖 ML training disabled - sklearn not available")
    
    def _load_calendar_patterns(self) -> Dict[str, Dict]:
        """Загрузить известные паттерны календарных багов"""
        return {
            "oauth_authentication_failure": {
                "symptoms": ["Invalid conference type value", "oauth", "credentials"],
                "severity": "high",
                "common_causes": ["expired tokens", "invalid scope", "missing refresh_token"],
                "fix_patterns": ["token refresh", "scope update", "re-authentication"]
            },
            "service_account_permission_error": {
                "symptoms": ["Service accounts cannot invite attendees", "forbidden", "permission"],
                "severity": "high", 
                "common_causes": ["missing domain delegation", "incorrect permissions", "calendar sharing"],
                "fix_patterns": ["domain delegation setup", "permission update", "calendar access"]
            },
            "conference_creation_failure": {
                "symptoms": ["Invalid conference type value", "hangoutLink", "conferenceData"],
                "severity": "medium",
                "common_causes": ["wrong conference type", "missing permissions", "API limitations"],
                "fix_patterns": ["use hangoutsMeet", "check permissions", "fallback strategy"]
            },
            "webhook_connection_timeout": {
                "symptoms": ["Connection timed out", "webhook", "timeout"],
                "severity": "critical",
                "common_causes": ["network issues", "server overload", "webhook conflicts"],
                "fix_patterns": ["clear webhook", "restart service", "check connectivity"]
            },
            "dual_calendar_sync_issue": {
                "symptoms": ["events not created", "only one calendar", "sync"],
                "severity": "medium",
                "common_causes": ["OAuth detection failure", "calendar ID issues", "permission mismatch"],
                "fix_patterns": ["fix OAuth detection", "validate calendar IDs", "check permissions"]
            }
        }
    
    def _initialize_with_known_patterns(self):
        """Инициализировать с известными паттернами багов"""
        session_id = "pattern_initialization"
        
        # Анализ текущих проблем из логов
        current_issues = self._analyze_current_issues()
        
        for issue in current_issues:
            bug_data = {
                'session_id': session_id,
                'bug_type': issue['type'],
                'severity': issue['severity'],
                'root_cause': issue['root_cause'],
                'code_features': issue['features'],
                'fix_applied': issue.get('suggested_fix', {}),
                'prevention_measures': issue.get('prevention', [])
            }
            self.history.save_bug(bug_data)
            
        logger.info(f"🧠 Initialized with {len(current_issues)} known calendar patterns")
    
    def _analyze_current_issues(self) -> List[Dict]:
        """Анализ текущих проблем на основе кода и логов"""
        issues = []
        
        # Проблема 1: OAuth vs Service Account detection
        issues.append({
            'type': 'oauth_detection_failure',
            'severity': 'high',
            'root_cause': 'Incorrect OAuth calendar detection leading to service account errors',
            'features': {
                'api_error_frequency': 0.8,
                'oauth_complexity': 0.9,
                'service_account_usage': 0.7,
                'error_handling_ratio': 0.3,
                'function_length': 85,
                'cyclomatic_complexity': 12
            },
            'suggested_fix': {
                'method': 'improve_oauth_detection',
                'confidence': 0.85
            },
            'prevention': ['better credential validation', 'explicit calendar type checking']
        })
        
        # Проблема 2: Conference type error
        issues.append({
            'type': 'conference_creation_failure', 
            'severity': 'medium',
            'root_cause': 'Using eventHangout instead of hangoutsMeet',
            'features': {
                'conference_creation': 0.9,
                'api_error_frequency': 0.6,
                'error_handling_ratio': 0.4,
                'function_length': 65,
                'cyclomatic_complexity': 8
            },
            'suggested_fix': {
                'method': 'use_hangouts_meet',
                'confidence': 0.95
            },
            'prevention': ['API documentation compliance', 'conference type validation']
        })
        
        # Проблема 3: Events not created in calendars
        issues.append({
            'type': 'dual_calendar_sync_issue',
            'severity': 'high', 
            'root_cause': 'Calendar detection and permission issues preventing event creation',
            'features': {
                'calendar_dual_mode': 0.85,
                'oauth_complexity': 0.7,
                'service_account_usage': 0.6,
                'error_handling_ratio': 0.2,
                'function_length': 120,
                'cyclomatic_complexity': 15
            },
            'suggested_fix': {
                'method': 'fix_calendar_detection_and_permissions',
                'confidence': 0.75
            },
            'prevention': ['comprehensive calendar testing', 'permission verification']
        })
        
        return issues
    
    def extract_calendar_features(self, code_str: str, error_logs: str = "") -> Dict[str, float]:
        """Извлечь признаки специфичные для календарной интеграции"""
        if not code_str:
            return self._get_default_calendar_features()
            
        features = {}
        
        # Базовые метрики кода
        features.update(self._extract_basic_code_features(code_str))
        
        # Календарные API признаки
        features['oauth_complexity'] = self._calculate_oauth_complexity(code_str)
        features['service_account_usage'] = self._calculate_service_account_usage(code_str)
        features['conference_creation'] = self._calculate_conference_complexity(code_str)
        features['calendar_dual_mode'] = self._calculate_dual_mode_complexity(code_str)
        features['api_error_frequency'] = self._analyze_error_patterns(error_logs)
        
        # Анализ ошибок
        features['webhook_issues'] = self._detect_webhook_issues(error_logs)
        features['permission_issues'] = self._detect_permission_issues(error_logs)
        features['authentication_issues'] = self._detect_auth_issues(error_logs)
        
        # Качество обработки ошибок
        features['error_handling_ratio'] = self._calculate_error_handling_ratio(code_str)
        features['fallback_mechanisms'] = self._count_fallback_mechanisms(code_str)
        
        logger.debug(f"🔍 Extracted features: {list(features.keys())}")
        return features
    
    def _extract_basic_code_features(self, code_str: str) -> Dict[str, float]:
        """Базовые метрики кода"""
        try:
            tree = ast.parse(code_str)
        except:
            return self._get_default_basic_features()
        
        lines = code_str.split('\n')
        
        return {
            'function_length': len(lines),
            'cyclomatic_complexity': self._calculate_cyclomatic_complexity(tree),
            'nesting_depth': self._calculate_max_nesting(tree),
            'variable_count': self._count_variables(tree),
            'comment_ratio': self._calculate_comment_ratio(code_str)
        }
    
    def _calculate_oauth_complexity(self, code_str: str) -> float:
        """Сложность OAuth интеграции"""
        oauth_patterns = [
            r'oauth_credentials', r'refresh_token', r'access_token',
            r'OAuth', r'credentials', r'_is_oauth', r'oauth_user'
        ]
        
        complexity = 0
        for pattern in oauth_patterns:
            matches = len(re.findall(pattern, code_str, re.IGNORECASE))
            complexity += matches * 0.1
        
        # Дополнительная сложность за условную логику OAuth
        if 'if.*oauth' in code_str.lower():
            complexity += 0.3
        if 'try.*oauth' in code_str.lower():
            complexity += 0.2
            
        return min(complexity, 1.0)
    
    def _calculate_service_account_usage(self, code_str: str) -> float:
        """Использование Service Account"""
        sa_patterns = [
            r'service_account', r'Service Account', r'ServiceAccount',
            r'google_service_account', r'credentials.*service'
        ]
        
        usage = 0
        for pattern in sa_patterns:
            matches = len(re.findall(pattern, code_str, re.IGNORECASE))
            usage += matches * 0.15
            
        return min(usage, 1.0)
    
    def _calculate_conference_complexity(self, code_str: str) -> float:
        """Сложность создания конференций"""
        conf_patterns = [
            r'conferenceData', r'hangoutLink', r'hangoutsMeet',
            r'eventHangout', r'conferenceDataVersion', r'createRequest'
        ]
        
        complexity = 0
        for pattern in conf_patterns:
            matches = len(re.findall(pattern, code_str))
            complexity += matches * 0.1
        
        # Штраф за использование устаревшего eventHangout
        if 'eventHangout' in code_str:
            complexity += 0.5
            
        return min(complexity, 1.0)
    
    def _calculate_dual_mode_complexity(self, code_str: str) -> float:
        """Сложность работы с двумя календарями"""
        dual_patterns = [
            r'manager_calendar', r'owner_calendar', r'dual.*calendar',
            r'both.*calendar', r'create.*both', r'manager_event_id', r'owner_event_id'
        ]
        
        complexity = 0
        for pattern in dual_patterns:
            matches = len(re.findall(pattern, code_str, re.IGNORECASE))
            complexity += matches * 0.1
            
        return min(complexity, 1.0)
    
    def _analyze_error_patterns(self, error_logs: str) -> float:
        """Анализ частоты ошибок в логах"""
        if not error_logs:
            return 0.0
            
        error_indicators = [
            'Invalid conference type value',
            'Service accounts cannot invite attendees',
            'Connection timed out',
            'Failed to create',
            'ERROR',
            'Exception'
        ]
        
        error_count = 0
        for indicator in error_indicators:
            error_count += error_logs.count(indicator)
        
        # Нормализация по длине логов
        if len(error_logs) > 0:
            frequency = error_count / (len(error_logs) / 1000)  # ошибок на 1000 символов
            return min(frequency, 1.0)
        
        return 0.0
    
    def _detect_webhook_issues(self, error_logs: str) -> float:
        """Обнаружение проблем с webhook"""
        webhook_issues = ['webhook', 'timeout', 'connection', 'failed to set']
        
        score = 0
        for issue in webhook_issues:
            if issue.lower() in error_logs.lower():
                score += 0.25
                
        return min(score, 1.0)
    
    def _detect_permission_issues(self, error_logs: str) -> float:
        """Обнаружение проблем с разрешениями"""
        permission_issues = [
            'forbidden', 'permission', 'access denied', 
            'cannot invite', 'not authorized'
        ]
        
        score = 0
        for issue in permission_issues:
            if issue.lower() in error_logs.lower():
                score += 0.2
                
        return min(score, 1.0)
    
    def _detect_auth_issues(self, error_logs: str) -> float:
        """Обнаружение проблем с аутентификацией"""
        auth_issues = [
            'authentication', 'credential', 'token', 
            'oauth', 'unauthorized', 'invalid'
        ]
        
        score = 0
        for issue in auth_issues:
            if issue.lower() in error_logs.lower():
                score += 0.15
                
        return min(score, 1.0)
    
    def _calculate_error_handling_ratio(self, code_str: str) -> float:
        """Соотношение обработки ошибок"""
        try_blocks = len(re.findall(r'\btry\b', code_str))
        except_blocks = len(re.findall(r'\bexcept\b', code_str))
        total_functions = len(re.findall(r'\bdef\b', code_str))
        
        if total_functions == 0:
            return 0.0
            
        error_handling = (try_blocks + except_blocks) / (total_functions * 2)
        return min(error_handling, 1.0)
    
    def _count_fallback_mechanisms(self, code_str: str) -> float:
        """Подсчет механизмов fallback"""
        fallback_patterns = [
            r'fallback', r'else:', r'except:', r'if.*failed',
            r'try.*except', r'alternative'
        ]
        
        count = 0
        for pattern in fallback_patterns:
            count += len(re.findall(pattern, code_str, re.IGNORECASE))
        
        return min(count * 0.1, 1.0)
    
    def predict_calendar_bug(self, code_features: Dict[str, float], 
                           error_context: str = "") -> Dict[str, Any]:
        """Предсказать вероятность календарного бага"""
        
        # Если sklearn недоступен, используем эвристический подход
        if not SKLEARN_AVAILABLE:
            return self._heuristic_prediction(code_features, error_context)
        
        # ML предсказание если доступно
        if any(self.models.values()):
            return self._ml_prediction(code_features)
        else:
            # Fallback к эвристике если модели не обучены
            return self._heuristic_prediction(code_features, error_context)
    
    def _heuristic_prediction(self, features: Dict[str, float], 
                            error_context: str) -> Dict[str, Any]:
        """Эвристическое предсказание на основе паттернов"""
        
        predictions = []
        
        # Анализ OAuth проблем
        oauth_risk = (features.get('oauth_complexity', 0) * 0.4 + 
                     features.get('authentication_issues', 0) * 0.6)
        if oauth_risk > 0.6:
            predictions.append({
                'bug_type': 'oauth_authentication_failure',
                'probability': oauth_risk,
                'confidence': 'medium',
                'evidence': 'High OAuth complexity and authentication issues detected'
            })
        
        # Анализ Service Account проблем  
        sa_risk = (features.get('service_account_usage', 0) * 0.3 +
                  features.get('permission_issues', 0) * 0.7)
        if sa_risk > 0.5:
            predictions.append({
                'bug_type': 'service_account_permission_error', 
                'probability': sa_risk,
                'confidence': 'medium',
                'evidence': 'Service account usage with permission issues'
            })
        
        # Анализ конференций
        conf_risk = features.get('conference_creation', 0)
        if conf_risk > 0.4 or 'Invalid conference type' in error_context:
            predictions.append({
                'bug_type': 'conference_creation_failure',
                'probability': max(conf_risk, 0.8 if 'Invalid conference type' in error_context else 0),
                'confidence': 'high' if 'Invalid conference type' in error_context else 'medium',
                'evidence': 'Conference creation complexity or known error pattern'
            })
        
        # Выбрать наиболее вероятную проблему
        if predictions:
            best_prediction = max(predictions, key=lambda x: x['probability'])
            
            # Добавить рекомендации
            best_prediction.update(self._generate_recommendations(best_prediction['bug_type']))
            
            return best_prediction
        else:
            return {
                'bug_type': 'unknown',
                'probability': 0.3,
                'confidence': 'low',
                'evidence': 'Insufficient indicators for specific bug type',
                'recommendations': ['Review error logs', 'Add more debugging', 'Check API documentation']
            }
    
    def _generate_recommendations(self, bug_type: str) -> Dict[str, Any]:
        """Генерировать рекомендации по исправлению"""
        
        recommendations_map = {
            'oauth_authentication_failure': {
                'immediate_actions': [
                    'Check OAuth token validity',
                    'Verify refresh_token presence',
                    'Validate OAuth scopes'
                ],
                'fixes': [
                    'Implement proper token refresh logic',
                    'Add OAuth credential validation',
                    'Update OAuth detection method'
                ],
                'prevention': [
                    'Add token expiration monitoring',
                    'Implement graceful OAuth failures',
                    'Add comprehensive OAuth testing'
                ]
            },
            'service_account_permission_error': {
                'immediate_actions': [
                    'Verify Service Account permissions',
                    'Check domain-wide delegation',
                    'Validate calendar sharing settings'
                ],
                'fixes': [
                    'Setup domain-wide delegation properly',
                    'Remove attendee invitations from SA calls',
                    'Use correct calendar access methods'
                ],
                'prevention': [
                    'Document Service Account limitations',
                    'Add permission verification before operations',
                    'Implement fallback for SA restrictions'
                ]
            },
            'conference_creation_failure': {
                'immediate_actions': [
                    'Change eventHangout to hangoutsMeet',
                    'Check conferenceDataVersion parameter',
                    'Verify Google Meet permissions'
                ],
                'fixes': [
                    'Update conference type to hangoutsMeet',
                    'Add conference creation fallback',
                    'Implement conference validation'
                ],
                'prevention': [
                    'Use consistent conference API',
                    'Add conference creation testing',
                    'Monitor Google API changes'
                ]
            }
        }
        
        return recommendations_map.get(bug_type, {
            'immediate_actions': ['Investigate error logs'],
            'fixes': ['Apply appropriate fix based on symptoms'],
            'prevention': ['Add monitoring and testing']
        })
    
    def _get_default_calendar_features(self) -> Dict[str, float]:
        """Значения по умолчанию для календарных признаков"""
        return {
            'api_error_frequency': 0.0,
            'oauth_complexity': 0.0,
            'calendar_dual_mode': 0.0,
            'conference_creation': 0.0,
            'service_account_usage': 0.0,
            'function_length': 50.0,
            'cyclomatic_complexity': 5.0,
            'error_handling_ratio': 0.5,
            'webhook_issues': 0.0,
            'permission_issues': 0.0,
            'authentication_issues': 0.0,
            'fallback_mechanisms': 0.3
        }
    
    def _get_default_basic_features(self) -> Dict[str, float]:
        """Базовые значения по умолчанию"""
        return {
            'function_length': 50.0,
            'cyclomatic_complexity': 5.0,
            'nesting_depth': 3.0,
            'variable_count': 10.0,
            'comment_ratio': 0.2
        }
    
    def _calculate_cyclomatic_complexity(self, tree) -> float:
        """Циклическая сложность"""
        complexity = 1  # базовая сложность
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                
        return float(complexity)
    
    def _calculate_max_nesting(self, tree) -> float:
        """Максимальная глубина вложенности"""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return float(get_depth(tree))
    
    def _count_variables(self, tree) -> float:
        """Подсчет переменных"""
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                variables.add(node.id)
        return float(len(variables))
    
    def _calculate_comment_ratio(self, code_str: str) -> float:
        """Соотношение комментариев"""
        lines = code_str.split('\n')
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines == 0:
            return 0.0
        return comment_lines / total_lines
    
    def load_or_train_models(self):
        """Загрузить или обучить ML модели"""
        if not SKLEARN_AVAILABLE:
            logger.warning("🤖 Sklearn not available - using heuristic approach only")
            return
            
        model_path = self.history.history_root / "calendar_ml_model.pkl"
        
        if model_path.exists():
            try:
                with open(model_path, 'rb') as f:
                    saved_data = joblib.load(f)
                    self.models = saved_data['models']
                    self.scaler = saved_data['scaler']
                    self.feature_importance = saved_data['feature_importance']
                logger.info("📚 Loaded existing ML models")
            except Exception as e:
                logger.error(f"❌ Failed to load models: {e}")
                self._train_initial_models()
        else:
            self._train_initial_models()
    
    def _train_initial_models(self):
        """Обучить начальные модели"""
        if not SKLEARN_AVAILABLE:
            return
            
        # Получить исторические данные
        bugs = self.history.get_all_bugs()
        
        if len(bugs) < 3:
            logger.info("🤖 Insufficient data for ML training - using heuristics only")
            return
        
        logger.info(f"🧠 Training ML models with {len(bugs)} historical bugs")
        
        # Подготовить данные для обучения
        X, y = self._prepare_training_data(bugs)
        
        if len(X) < 3:
            logger.warning("⚠️ Not enough training samples")
            return
        
        # Обучить модель
        self.models['general_bugs'] = RandomForestClassifier(
            n_estimators=20,  # Уменьшено для малых данных
            max_depth=5,
            min_samples_split=2,
            random_state=42
        )
        
        # Нормализация
        X_scaled = self.scaler.fit_transform(X)
        
        # Обучение
        self.models['general_bugs'].fit(X_scaled, y)
        
        # Сохранить модель
        self._save_models()
        
        logger.info("✅ ML models trained and saved")
    
    def _prepare_training_data(self, bugs: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Подготовить данные для обучения"""
        X = []
        y = []
        
        for bug in bugs:
            features = bug.get('code_features', {})
            if features:
                # Конвертировать в вектор признаков
                feature_vector = self._dict_to_vector(features)
                X.append(feature_vector)
                y.append(bug.get('bug_type', 'unknown'))
        
        return np.array(X), np.array(y)
    
    def _dict_to_vector(self, features: Dict[str, float]) -> List[float]:
        """Конвертировать словарь признаков в вектор"""
        expected_features = [
            'api_error_frequency', 'oauth_complexity', 'calendar_dual_mode',
            'conference_creation', 'service_account_usage', 'function_length',
            'cyclomatic_complexity', 'error_handling_ratio', 'webhook_issues',
            'permission_issues', 'authentication_issues', 'fallback_mechanisms'
        ]
        
        return [features.get(feature, 0.0) for feature in expected_features]
    
    def _save_models(self):
        """Сохранить обученные модели"""
        if not SKLEARN_AVAILABLE:
            return
            
        model_path = self.history.history_root / "calendar_ml_model.pkl"
        
        save_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_importance': self.feature_importance,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(model_path, 'wb') as f:
                joblib.dump(save_data, f)
            logger.info(f"💾 Models saved to {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save models: {e}")


def create_calendar_ml_system(project_path: str) -> CalendarIntegrationMLPredictor:
    """Создать и инициализировать ML систему для календарной интеграции"""
    
    # Создать директорию для диагностической системы
    diagnostic_dir = Path(project_path) / "src" / "diagnostic_system"
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    
    # Создать __init__.py файл
    init_file = diagnostic_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Diagnostic System Package")
    
    # Инициализировать историю
    history = MandatoryHistoryPersistence(project_path)
    
    # Создать ML предсказатель
    ml_predictor = CalendarIntegrationMLPredictor(history)
    
    logger.info("🚀 Calendar ML system initialized")
    return ml_predictor