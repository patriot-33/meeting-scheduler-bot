# 🚀 Deployment Checklist - Meeting Scheduler Bot

## Pre-Deployment Setup

### 1. Environment Variables (Required)
Create `.env` file with:
```bash
# Telegram Bot (get from @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Admin Telegram IDs (comma separated, get from @userinfobot)
ADMIN_TELEGRAM_IDS=123456789,987654321

# Database (Render PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google Calendar IDs
GOOGLE_CALENDAR_ID_1=your-email@gmail.com
GOOGLE_CALENDAR_ID_2=partner-email@gmail.com

# Optional: Webhook for production
WEBHOOK_URL=https://your-app.onrender.com
```

### 2. Google Service Account
- Create service account in Google Cloud Console
- Download `service_account_key.json`
- Share calendars with service account email

### 3. Dependencies
```bash
pip install -r requirements.txt
```

## Deployment Steps

### 1. Health Check
```bash
python run_health_check.py
```

### 2. Local Test (Optional)
```bash
# Set DEBUG=true in .env
python -m src.main
```

### 3. Deploy to Render
- Connect GitHub repo
- Set environment variables
- Add `service_account_key.json` content to `GOOGLE_SERVICE_ACCOUNT_FILE`
- Deploy

## Quick Verification

### After Deployment:
1. ✅ Bot responds to `/start` command
2. ✅ Admin can see pending users with `/pending`
3. ✅ Regular user can register
4. ✅ Manager can see available slots with `/schedule`
5. ✅ Health check endpoint works (if implemented)

## Team-Specific Configuration

**For 7-person team:**
- `pool_size=5` (database connections)
- `reminder_intervals: [7, 3, 1]` (days before meeting)
- `available_slots: ["11:00", "14:00", "15:00", "16:00", "17:00"]`
- Scheduler checks every 15 minutes
- Single job instance (no concurrency issues)

## Troubleshooting

### Common Issues:
1. **Database connection failed**: Check DATABASE_URL format
2. **Bot token invalid**: Regenerate token from @BotFather
3. **Google Calendar access denied**: Check service account permissions
4. **No admin privileges**: Verify ADMIN_TELEGRAM_IDS

### Log Locations:
- Render: Dashboard → Logs
- Local: `bot.log` (if DEBUG=true)

## Support Commands

```bash
# Health check
python run_health_check.py

# Test imports
python -c "from src.main import main; print('✅ Imports OK')"

# Test database
python -c "from src.database import init_db; init_db(); print('✅ Database OK')"
```