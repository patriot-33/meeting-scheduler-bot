from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from datetime import datetime, timedelta
import logging
import pytz

from src.config import settings
from src.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

def setup_scheduler(application):
    """Setup APScheduler for reminders."""
    
    # Configure scheduler
    jobstores = {
        'default': MemoryJobStore()
    }
    executors = {
        'default': AsyncIOExecutor()
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=pytz.timezone(settings.timezone)
    )
    
    # Add periodic job to process reminders
    scheduler.add_job(
        func=process_reminders,
        trigger="interval",
        minutes=30,  # Check every 30 minutes
        args=[application],
        id='reminder_processor',
        replace_existing=True
    )
    
    # Add job to check for overdue meetings
    scheduler.add_job(
        func=check_overdue_meetings,
        trigger="cron",
        hour=9,  # Check at 9 AM daily
        args=[application],
        id='overdue_checker',
        replace_existing=True
    )
    
    return scheduler

async def process_reminders(application):
    """Process pending reminders."""
    try:
        reminder_service = ReminderService()
        await reminder_service.process_pending_reminders(application.bot)
        logger.info("Processed pending reminders")
    except Exception as e:
        logger.error(f"Error processing reminders: {e}")

async def check_overdue_meetings(application):
    """Check for overdue meetings and notify admins."""
    try:
        reminder_service = ReminderService()
        await reminder_service.check_overdue_meetings(application.bot)
        logger.info("Checked overdue meetings")
    except Exception as e:
        logger.error(f"Error checking overdue meetings: {e}")