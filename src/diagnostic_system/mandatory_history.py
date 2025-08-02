"""
MANDATORY HISTORY PERSISTENCE SYSTEM v4.0
Критически важная система сохранения ВСЕЙ истории диагностики и исправлений
"""
import json
import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
import hashlib
import shutil
from typing import Dict, List, Any, Optional
import logging
import traceback
import os

logger = logging.getLogger(__name__)

class MandatoryHistoryPersistence:
    """КРИТИЧЕСКИ ВАЖНО: Система обязательного сохранения ВСЕЙ истории"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.history_root = self.project_root / ".diagnostic_history"
        self.history_root.mkdir(exist_ok=True)
        
        # Множественные системы хранения для надежности
        self.db_path = self.history_root / "diagnostic_history.db"
        self.json_backup = self.history_root / "history_backup.json"
        self.pickle_backup = self.history_root / "history_backup.pkl"
        
        # Инициализация БД
        self._init_database()
        
        # Автоматический бэкап
        self.backup_manager = AutoBackupManager(self.history_root)
        
        logger.info(f"🏛️ MandatoryHistoryPersistence initialized at {self.history_root}")
        
    def _init_database(self):
        """Инициализация SQLite БД для истории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица сессий диагностики
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostic_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                problem_description TEXT,
                final_status TEXT,
                full_data TEXT
            )
        """)
        
        # Таблица всех изменений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS changes (
                change_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                file_path TEXT,
                change_type TEXT,
                diff_content TEXT,
                metrics_before TEXT,
                metrics_after TEXT,
                rollback_info TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
            )
        """)
        
        # Таблица багов - КРИТИЧЕСКИ ВАЖНО для ML
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bugs (
                bug_id TEXT PRIMARY KEY,
                session_id TEXT,
                discovery_time TIMESTAMP,
                bug_type TEXT,
                severity TEXT,
                root_cause TEXT,
                fix_applied TEXT,
                prevention_measures TEXT,
                code_features TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
            )
        """)
        
        # Таблица паттернов для ML обучения
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_signature TEXT,
                occurrences INTEGER,
                last_seen TIMESTAMP,
                fix_strategy TEXT,
                success_rate REAL
            )
        """)
        
        # Таблица предсказаний ML
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                prediction_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                predicted_bug_type TEXT,
                confidence REAL,
                actual_outcome TEXT,
                feature_vector TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
            )
        """)
        
        # Таблица метрик системы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                metric_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                metric_type TEXT,
                metric_value REAL,
                context_data TEXT,
                FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized with all required tables")
    
    def save_session_start(self, session_data: Dict[str, Any]) -> str:
        """ОБЯЗАТЕЛЬНОЕ сохранение начала сессии диагностики"""
        session_id = session_data.get('session_id', self._generate_id("session"))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO diagnostic_sessions (
                session_id, start_time, problem_description, full_data
            ) VALUES (?, ?, ?, ?)
        """, (
            session_id,
            datetime.now().isoformat(),
            session_data.get('problem_description', ''),
            json.dumps(session_data)
        ))
        
        conn.commit()
        conn.close()
        
        # Бэкапы
        self._append_to_json_backup('sessions', session_data)
        self._save_to_pickle_backup('session_start', session_id, session_data)
        
        logger.info(f"💾 Session {session_id} started and saved")
        return session_id
    
    def save_bug(self, bug_data: Dict[str, Any]) -> str:
        """ОБЯЗАТЕЛЬНОЕ сохранение информации о баге для ML"""
        bug_id = self._generate_id("bug")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bugs (
                bug_id, session_id, discovery_time, bug_type,
                severity, root_cause, fix_applied, prevention_measures,
                code_features
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bug_id,
            bug_data.get('session_id'),
            datetime.now().isoformat(),
            bug_data.get('bug_type'),
            bug_data.get('severity'),
            bug_data.get('root_cause'),
            json.dumps(bug_data.get('fix_applied', {})),
            json.dumps(bug_data.get('prevention_measures', [])),
            json.dumps(bug_data.get('code_features', {}))
        ))
        
        conn.commit()
        conn.close()
        
        # Бэкапы
        self._append_to_json_backup('bugs', bug_data)
        self._save_to_pickle_backup('bug', bug_id, bug_data)
        
        logger.info(f"🐛 Bug {bug_id} saved: {bug_data.get('bug_type')}")
        return bug_id
    
    def save_ml_prediction(self, prediction_data: Dict[str, Any]) -> str:
        """Сохранить предсказание ML для обучения"""
        prediction_id = self._generate_id("prediction")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ml_predictions (
                prediction_id, session_id, timestamp, predicted_bug_type,
                confidence, actual_outcome, feature_vector
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_id,
            prediction_data.get('session_id'),
            datetime.now().isoformat(),
            prediction_data.get('predicted_bug_type'),
            prediction_data.get('confidence', 0.0),
            prediction_data.get('actual_outcome'),
            json.dumps(prediction_data.get('feature_vector', {}))
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🤖 ML prediction {prediction_id} saved")
        return prediction_id
    
    def get_all_bugs(self) -> List[Dict[str, Any]]:
        """Получить все сохраненные баги для обучения ML"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT bug_id, bug_type, severity, root_cause, 
                   code_features, discovery_time
            FROM bugs 
            ORDER BY discovery_time DESC
        """)
        
        bugs = []
        for row in cursor.fetchall():
            bug = {
                'bug_id': row[0],
                'bug_type': row[1],
                'severity': row[2],
                'root_cause': row[3],
                'code_features': json.loads(row[4]) if row[4] else {},
                'discovery_time': row[5]
            }
            bugs.append(bug)
        
        conn.close()
        logger.info(f"📊 Retrieved {len(bugs)} bugs for ML training")
        return bugs
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получить полные данные сессии"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT full_data FROM diagnostic_sessions 
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def _generate_id(self, prefix: str) -> str:
        """Генерация уникального ID"""
        timestamp = datetime.now().isoformat()
        hash_part = hashlib.md5(f"{timestamp}{prefix}".encode()).hexdigest()[:8]
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash_part}"
    
    def _append_to_json_backup(self, data_type: str, data: Dict[str, Any]):
        """Добавить в JSON бэкап"""
        backup_file = self.history_root / f"{data_type}_backup.json"
        
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        
        existing_data.append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    def _save_to_pickle_backup(self, data_type: str, item_id: str, data: Dict[str, Any]):
        """Сохранить в pickle бэкап"""
        pickle_dir = self.history_root / "pickle_backups"
        pickle_dir.mkdir(exist_ok=True)
        
        pickle_file = pickle_dir / f"{data_type}_{item_id}.pkl"
        
        with open(pickle_file, 'wb') as f:
            pickle.dump({
                'timestamp': datetime.now().isoformat(),
                'data_type': data_type,
                'item_id': item_id,
                'data': data
            }, f)
    
    def _log_error(self, message: str):
        """Логирование ошибок"""
        logger.error(message)
        
        # Также сохранить в файл ошибок
        error_file = self.history_root / "errors.log"
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")


class AutoBackupManager:
    """Автоматическое резервное копирование"""
    
    def __init__(self, history_root: Path):
        self.history_root = history_root
        self.backup_root = history_root / "backups"
        self.backup_root.mkdir(exist_ok=True)
        
    def create_snapshot(self):
        """Создать снимок всей истории"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_dir = self.backup_root / f"snapshot_{timestamp}"
        
        try:
            # Копировать все файлы истории (кроме папки backups)
            for item in self.history_root.iterdir():
                if item.name != "backups" and item.is_file():
                    dest_file = snapshot_dir / item.name
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_file)
                elif item.name != "backups" and item.is_dir():
                    dest_dir = snapshot_dir / item.name
                    shutil.copytree(item, dest_dir)
            
            # Сжать старые бэкапы
            self._compress_old_backups()
            
            logger.info(f"📸 Created backup snapshot: {snapshot_dir}")
            
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
    
    def _compress_old_backups(self):
        """Сжать бэкапы старше 7 дней"""
        import zipfile
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for backup_dir in self.backup_root.iterdir():
            if (backup_dir.is_dir() and 
                backup_dir.stat().st_mtime < cutoff_date.timestamp()):
                
                zip_path = backup_dir.with_suffix('.zip')
                try:
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for file in backup_dir.rglob('*'):
                            if file.is_file():
                                zf.write(file, file.relative_to(backup_dir))
                    shutil.rmtree(backup_dir)
                    logger.info(f"🗜️ Compressed old backup: {zip_path}")
                except Exception as e:
                    logger.error(f"❌ Compression failed for {backup_dir}: {e}")