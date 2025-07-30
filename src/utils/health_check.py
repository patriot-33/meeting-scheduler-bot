"""Simple health check utility for small team deployment."""
import logging
from datetime import datetime
from sqlalchemy import text
from src.database import engine
from src.config import settings

logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database is accessible."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database OK"
    except Exception as e:
        return False, f"Database error: {str(e)[:100]}"

def check_config():
    """Check if required config is present."""
    try:
        required_fields = [
            settings.telegram_bot_token,
            settings.database_url,
            settings.admin_telegram_ids
        ]
        
        if all(required_fields):
            return True, "Config OK"
        else:
            return False, "Missing required config"
    except Exception as e:
        return False, f"Config error: {str(e)[:100]}"

def health_check():
    """Run all health checks."""
    checks = {
        'timestamp': datetime.now().isoformat(),
        'database': check_database_connection(),
        'config': check_config()
    }
    
    all_ok = all(check[0] for check in checks.values() if isinstance(check, tuple))
    
    return {
        'status': 'healthy' if all_ok else 'unhealthy',
        'checks': {k: {'status': v[0], 'message': v[1]} if isinstance(v, tuple) else v 
                  for k, v in checks.items()}
    }

if __name__ == '__main__':
    import json
    print(json.dumps(health_check(), indent=2))