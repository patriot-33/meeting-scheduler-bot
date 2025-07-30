from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import func
import logging

from database import get_db, User, Meeting, UserRole, UserStatus, MeetingStatus
from config import settings
from utils.decorators import require_admin

logger = logging.getLogger(__name__)

@require_admin
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu."""
    keyboard = [
        [
            InlineKeyboardButton("=e >;L7>20B5;8", callback_data="admin_users"),
            InlineKeyboardButton("S 6840NI85", callback_data="admin_pending")
        ],
        [
