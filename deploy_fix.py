#!/usr/bin/env python3
"""
🚀 DEPLOYMENT FIX for Render.com
Автоматически применяет критичную миграцию при deploy

Интегрируется в процесс запуска для автоматического исправления
column meetings.google_calendar_id does not exist
"""

import os
import sys
import logging

# Setup logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DEPLOY_FIX - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_critical_migration():
    """Run critical migration during deployment"""
    logger.info("🚀 DEPLOYMENT FIX: Running critical migration")
    
    try:
        # Check if we're in production environment
        environment = os.getenv('ENVIRONMENT', 'development')
        logger.info(f"Environment: {environment}")
        
        # Import and run migration directly
        from migrations.add_google_calendar_id_field import upgrade
        
        logger.info("🔧 Applying google_calendar_id migration...")
        success = upgrade()
        
        if success:
            logger.info("✅ Deployment fix successful")
            return True
        else:
            logger.error("❌ Deployment fix failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Deployment fix error: {e}")
        # Don't fail deployment, just log the error
        logger.warning("⚠️ Continuing deployment despite migration error")
        return False

if __name__ == "__main__":
    # This can be called from main.py during startup
    run_critical_migration()