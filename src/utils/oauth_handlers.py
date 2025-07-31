"""
OAuth callback handlers for web endpoints
"""
import logging
from aiohttp import web as aio_web

logger = logging.getLogger(__name__)

async def oauth_callback_handler(request, application):
    """Handle OAuth callback for manager calendar integration."""
    try:
        from services.oauth_service import oauth_service
        
        # Get authorization code and state from query parameters
        code = request.query.get('code')
        state = request.query.get('state')
        error = request.query.get('error')
        
        if error:
            logger.error(f"OAuth error: {error}")
            return aio_web.Response(
                text="🙁 Ошибка подключения календаря. Попробуйте еще раз.",
                content_type='text/html; charset=utf-8',
                status=400
            )
        
        if not code or not state:
            return aio_web.Response(
                text="❌ Неверные параметры OAuth",
                content_type='text/html; charset=utf-8',
                status=400
            )
        
        # Handle OAuth callback
        result = oauth_service.handle_oauth_callback(code, state)
        
        if result['success']:
            # Notify user via Telegram
            telegram_id = result['telegram_id']
            email = result['email']
            
            try:
                await application.bot.send_message(
                    chat_id=telegram_id,
                    text=f"✅ **Google Calendar успешно подключен!**\\n\\n"
                         f"📧 Календарь: {email}\\n"
                         f"🎉 Теперь вы можете планировать встречи!\\n\\n"
                         f"Используйте /schedule для начала.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify user about successful OAuth: {e}")
            
            return aio_web.Response(
                text="✅ <h1>Календарь успешно подключен!</h1><p>Возвращайтесь в Телеграм бот для планирования встреч.</p>",
                content_type='text/html',
                charset='utf-8'
            )
        else:
            logger.error(f"OAuth callback failed: {result.get('error')}")
            return aio_web.Response(
                text=f"❌ <h1>Ошибка подключения</h1><p>{result.get('error', 'Неизвестная ошибка')}</p>",
                content_type='text/html',
                charset='utf-8',
                status=400
            )
        
    except Exception as e:
        logger.error(f"OAuth callback handler error: {e}")
        return aio_web.Response(
            text="❌ Внутренняя ошибка сервера",
            content_type='text/html',
            charset='utf-8',
            status=500
        )