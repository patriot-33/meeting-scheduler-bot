"""
🛡️ TELEGRAM SAFE MESSAGING UTILITIES
Comprehensive defensive programming utilities for safe Telegram API interactions.
Prevents BadRequest, infinite recursion, and other issues that were previously encountered.

Based on lessons learned from:
- ENV_LOADING_001: Environment variable loading issues
- BADREQUEST_002: Message is not modified errors  
- INFINITE_RECURSION_004: Recursive function calls
- CALENDAR_STATUS_003: Unclear error messages
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from functools import wraps
import traceback
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, NetworkError, TimedOut, Forbidden, TelegramError

logger = logging.getLogger(__name__)

class TelegramSafeError(Exception):
    """Custom exception for Telegram safe operations"""
    pass

class MessageTracker:
    """Track messages to prevent duplicate operations"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minute TTL
        self.message_cache: Dict[str, datetime] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def is_duplicate(self, chat_id: int, message_text: str, markup_str: str = "") -> bool:
        """Check if this message+markup combination was recently sent"""
        key = f"{chat_id}:{hash(message_text + markup_str)}"
        now = datetime.now()
        
        # Clean expired entries
        expired_keys = [k for k, timestamp in self.message_cache.items() 
                       if now - timestamp > self.ttl]
        for k in expired_keys:
            del self.message_cache[k]
        
        # Check if this combination exists
        if key in self.message_cache:
            return True
        
        # Record this combination
        self.message_cache[key] = now
        return False

# Global message tracker to prevent duplicates
_message_tracker = MessageTracker()

def recursion_guard(max_depth: int = 10):
    """
    Decorator to prevent infinite recursion in functions.
    Addresses INFINITE_RECURSION_004 issue type.
    """
    def decorator(func):
        # Use function-specific counter to track recursion depth
        if not hasattr(func, '_recursion_depth'):
            func._recursion_depth = 0
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func._recursion_depth += 1
            
            if func._recursion_depth > max_depth:
                logger.error(f"🚨 Recursion limit exceeded in {func.__name__} (depth: {func._recursion_depth})")
                func._recursion_depth -= 1
                raise TelegramSafeError(f"Maximum recursion depth exceeded in {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                func._recursion_depth -= 1
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func._recursion_depth += 1
            
            if func._recursion_depth > max_depth:
                logger.error(f"🚨 Recursion limit exceeded in {func.__name__} (depth: {func._recursion_depth})")
                func._recursion_depth -= 1
                raise TelegramSafeError(f"Maximum recursion depth exceeded in {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                func._recursion_depth -= 1
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def telegram_safe(max_retries: int = 3, backoff_factor: float = 1.0):
    """
    Enhanced decorator for safe Telegram API operations with comprehensive error handling.
    
    Implements defensive measures for:
    - BadRequest: Message is not modified errors (BADREQUEST_002)
    - Network timeouts and connection issues
    - Telegram API rate limiting
    - Automatic retry with exponential backoff
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"🔄 Retry attempt {attempt} for {func.__name__}")
                    
                    return await func(*args, **kwargs)
                    
                except BadRequest as e:
                    error_msg = str(e).lower()
                    
                    if "message is not modified" in error_msg:
                        logger.debug(f"📨 Message not modified (expected): {func.__name__}")
                        return {"status": "not_modified", "reason": "identical_content"}
                    elif "message can't be edited" in error_msg:
                        logger.warning(f"⚠️ Message can't be edited: {func.__name__}")
                        return {"status": "edit_failed", "reason": "message_too_old"}
                    elif "chat not found" in error_msg:
                        logger.error(f"❌ Chat not found: {func.__name__}")
                        return {"status": "error", "reason": "chat_not_found"}
                    else:
                        logger.error(f"❌ BadRequest in {func.__name__}: {e}")
                        last_exception = e
                        
                except (NetworkError, TimedOut) as e:
                    logger.warning(f"🌐 Network error in {func.__name__} (attempt {attempt + 1}): {e}")
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.info(f"⏳ Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                        
                except Forbidden as e:
                    logger.error(f"🚫 Forbidden error in {func.__name__}: {e}")
                    return {"status": "error", "reason": "forbidden", "details": str(e)}
                    
                except TelegramError as e:
                    logger.error(f"❌ Telegram error in {func.__name__}: {e}")
                    last_exception = e
                    
                except Exception as e:
                    logger.error(f"💥 Unexpected error in {func.__name__}: {e}")
                    logger.error(f"📊 Stack trace: {traceback.format_exc()}")
                    last_exception = e
                    
                # If we get here, an error occurred
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
            
            # All retries failed
            logger.error(f"💥 All retries failed for {func.__name__}: {last_exception}")
            return {"status": "error", "reason": "max_retries_exceeded", "details": str(last_exception)}
        
        return wrapper
    return decorator

@telegram_safe(max_retries=2)
@recursion_guard(max_depth=5)
async def safe_send_message(update_or_context, text, reply_markup=None, parse_mode='Markdown', chat_id=None, force_send=False):
    """
    Enhanced universal safe message sending with comprehensive error handling.
    
    Implements defensive measures for:
    - BADREQUEST_002: Message is not modified errors
    - INFINITE_RECURSION_004: Recursive function calls
    - Network issues and timeouts
    - Duplicate message prevention
    
    Args:
        update_or_context: Update object or Context for direct sending
        text: Message text
        reply_markup: Keyboard (optional)
        parse_mode: Parse mode (default Markdown)
        chat_id: Chat ID for direct sending (if using context)
    
    Returns:
        Dict with status and result information
    """
    if not text or not text.strip():
        logger.warning("⚠️ Attempting to send empty message")
        return {"status": "error", "reason": "empty_message"}
    
    # Check for duplicate messages to prevent spam
    markup_str = str(reply_markup) if reply_markup else ""
    effective_chat_id = None
    
    if hasattr(update_or_context, 'effective_chat') and update_or_context.effective_chat:
        effective_chat_id = update_or_context.effective_chat.id
    elif chat_id:
        effective_chat_id = chat_id
    
    if not force_send and effective_chat_id and _message_tracker.is_duplicate(effective_chat_id, text, markup_str):
        logger.info("📨 Duplicate message detected, preventing spam")
        return {"status": "duplicate_prevented"}
    
    try:
        # Determine input parameter type and send appropriately
        if hasattr(update_or_context, 'callback_query') and update_or_context.callback_query:
            # This is Update with callback query - use edit_message_text
            logger.debug(f"📝 Editing message via callback: {text[:50]}...")
            
            message = await update_or_context.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            
            # Answer callback query to remove loading state
            try:
                await update_or_context.callback_query.answer()
            except Exception as callback_error:
                logger.warning(f"⚠️ Could not answer callback query: {callback_error}")
            
            return {"status": "edited", "message": message}
            
        elif hasattr(update_or_context, 'message') and update_or_context.message:
            # This is Update with regular message - use reply_text
            logger.debug(f"📤 Replying to message: {text[:50]}...")
            
            message = await update_or_context.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            
            return {"status": "sent", "message": message}
            
        elif hasattr(update_or_context, 'bot') and chat_id:
            # This is Context - use direct sending
            logger.debug(f"📤 Sending direct message to {chat_id}: {text[:50]}...")
            
            message = await update_or_context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            
            return {"status": "sent", "message": message}
            
        else:
            # Auto-detection attempt
            logger.warning(f"⚠️ Unclear update type: {type(update_or_context)}")
            
            if hasattr(update_or_context, 'effective_chat'):
                logger.debug("🔍 Using effective_chat for sending")
                
                message = await update_or_context.effective_chat.send_message(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                
                return {"status": "sent", "message": message}
            else:
                error_msg = f"Cannot determine how to send message with {type(update_or_context)}"
                logger.error(f"❌ {error_msg}")
                return {"status": "error", "reason": "unknown_context_type", "details": error_msg}
                
    except Exception as e:
        # Let the telegram_safe decorator handle this
        logger.error(f"💥 Error in safe_send_message: {e}")
        raise

async def safe_edit_message(query, text, reply_markup=None, parse_mode='Markdown'):
    """Безопасное редактирование сообщения через callback query"""
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified - ignoring")
            return
        else:
            logger.error(f"BadRequest error in edit_message: {e}")
            raise
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        raise

async def safe_reply_text(message, text, reply_markup=None, parse_mode='Markdown'):
    """Безопасный ответ на сообщение"""
    try:
        await message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified - ignoring")
            return
        else:
            logger.error(f"BadRequest error in reply_text: {e}")
            raise
    except Exception as e:
        logger.error(f"Error replying to message: {e}")
        raise

async def safe_context_send(context, chat_id, text, reply_markup=None, parse_mode='Markdown'):
    """Безопасная отправка через контекст"""
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message not modified - ignoring")
            return
        else:
            logger.error(f"BadRequest error in context send: {e}")
            raise
    except Exception as e:
        logger.error(f"Error sending via context: {e}")
        raise