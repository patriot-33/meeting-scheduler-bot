"""
Обработчики для подключения Google Calendar руководителями
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_db, User, UserRole
from utils.decorators import require_registration
from config import settings

logger = logging.getLogger(__name__)

@require_registration
async def connect_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Инструкция по подключению Google Calendar для руководителей."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if user.role != UserRole.MANAGER:
            await update.message.reply_text(
                "❌ Данная функция доступна только руководителям отделов."
            )
            return
    
    instructions = """
📅 **Подключение Google Calendar**

Для участия во встречах через Google Meet вам необходимо:

1️⃣ **Убедитесь, что у вас есть Google аккаунт**
   • Если нет - создайте на google.com
   • Используйте корпоративную почту, если возможно

2️⃣ **Сообщите свой email владельцу бизнеса**
   • Владелец добавит вас как участника встречи
   • Вы получите приглашение на почту

3️⃣ **Примите приглашение на встречу**
   • Откройте письмо от Google Calendar
   • Нажмите "Да, я приду"
   • Встреча появится в вашем календаре

4️⃣ **За час до встречи**
   • Вы получите напоминание в боте
   • В календаре будет ссылка на Google Meet
   • Просто нажмите на ссылку для подключения

💡 **Советы:**
• Установите приложение Google Calendar на телефон
• Включите уведомления в приложении
• Проверьте работу микрофона и камеры заранее
• Подключайтесь за 5 минут до начала

❓ **Возникли проблемы?**
Обратитесь к владельцу бизнеса или IT-отделу.
"""
    
    keyboard = [
        [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
        [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        instructions, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback для календаря."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "send_email_to_owner":
        await send_email_prompt(update, context)
    elif query.data == "calendar_faq":
        await show_calendar_faq(update, context)

async def send_email_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос email для отправки владельцу."""
    text = """
📧 **Отправка email владельцу**

Введите ваш Google email в формате:
`ваше_имя@gmail.com` или `ваше_имя@компания.ru`

Владелец получит уведомление и добавит вас в календарь.

💡 Используйте команду:
`/email ваш_email@gmail.com`
"""
    
    keyboard = [[InlineKeyboardButton("← Назад", callback_data="connect_calendar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def save_manager_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить email менеджера и уведомить владельца."""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите email после команды.\n"
            "Пример: `/email john.doe@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    email = context.args[0]
    
    # Простая проверка email
    if '@' not in email or '.' not in email.split('@')[1]:
        await update.message.reply_text(
            "❌ Неверный формат email.\n"
            "Пример: `john.doe@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user or user.role != UserRole.MANAGER:
            await update.message.reply_text("❌ Функция доступна только руководителям.")
            return
        
        # Сохраняем email
        user.email = email
        db.commit()
        
        # Уведомляем владельцев
        owners = db.query(User).filter(User.role == UserRole.OWNER).all()
        
        notification_text = f"""
📧 **Новый email руководителя**

👤 {user.first_name} {user.last_name}
🏢 Отдел: {user.department.value}
📧 Email: {email}

Руководитель запросил подключение к Google Calendar.
Добавьте этот email в календарь для участия во встречах.
"""
        
        for owner in owners:
            try:
                await context.bot.send_message(
                    chat_id=owner.telegram_id,
                    text=notification_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify owner {owner.id}: {e}")
    
    await update.message.reply_text(
        f"✅ Email сохранен: `{email}`\n\n"
        f"Владельцы получили уведомление и добавят вас в календарь.\n"
        f"Вы получите приглашение на указанную почту.",
        parse_mode='Markdown'
    )

async def show_calendar_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать частые вопросы по календарю."""
    faq_text = """
❓ **Частые вопросы по Google Calendar**

**Q: Нужен ли платный аккаунт Google?**
A: Нет, достаточно бесплатного аккаунта Gmail.

**Q: Могу ли я использовать корпоративную почту?**
A: Да, если она подключена к Google Workspace.

**Q: Как изменить email?**
A: Используйте команду `/email новый_email@gmail.com`

**Q: Не приходит приглашение**
A: Проверьте папку "Спам" и правильность email.

**Q: Можно ли подключиться с телефона?**
A: Да, через приложение Google Meet или браузер.

**Q: Нужна ли камера для встречи?**
A: Желательно, но не обязательно. Можно участвовать только с микрофоном.

**Q: Как отменить участие во встрече?**
A: Используйте команду `/my_meetings` и отмените встречу.

**Q: Встреча не отображается в календаре**
A: Убедитесь, что приняли приглашение в письме.
"""
    
    keyboard = [[InlineKeyboardButton("← Назад", callback_data="connect_calendar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        faq_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )