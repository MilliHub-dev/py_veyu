# Vercel Logging Guide

## The Issue
The Veyu Log Viewer at `/logs/` is designed to read log files from the local filesystem. However, on Vercel (serverless), logs are not stored in files - they're streamed to stdout/stderr and captured by Vercel's logging infrastructure.

## How to View Logs on Vercel

### 1. Vercel Dashboard (Recommended)
- Go to https://vercel.com/dashboard
- Select your project
- Click on "Logs" tab
- Filter by deployment, function, or time range

### 2. Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# View real-time logs
vercel logs [deployment-url]

# View logs for production
vercel logs --prod

# Follow logs in real-time
vercel logs --follow
```

### 3. Log Aggregation Services
Integrate with a log aggregation service for better log management:

#### Option A: Datadog
```python
# Install: pip install ddtrace
# Add to settings.py:
LOGGING['handlers']['datadog'] = {
    'level': 'INFO',
    'class': 'logging.StreamHandler',
}
```

#### Option B: LogDNA/Mezmo
```python
# Install: pip install logdna
# Configure in settings.py
```

#### Option C: Sentry
```python
# Install: pip install sentry-sdk
# Add to settings.py:
import sentry_sdk
sentry_sdk.init(dsn="your-dsn-here")
```

## Current Logging Configuration
The application is configured to log to:
- **Console (stdout)** - Captured by Vercel ✅
- **File** - Only works locally, not on Vercel ❌

## Recommended Changes

### Update settings.py to detect Vercel environment:
```python
import os

IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False)

if IS_VERCEL:
    # On Vercel, only use console logging
    LOGGING['handlers'] = {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    }
else:
    # Local development - use file logging
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'logs' / 'application.log',
        'formatter': 'verbose',
    }
```

## Viewing Application Logs

### Django Request Logs
Django automatically logs to stdout, which Vercel captures. Check Vercel dashboard for:
- Request paths
- Response status codes
- Error tracebacks

### Custom Application Logs
Use Python's logging module:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("User logged in")
logger.error("Payment failed", extra={'user_id': user.id})
```

## Troubleshooting

### Logs not appearing?
1. Ensure logging is configured to use StreamHandler (console)
2. Check log level is not too restrictive (use INFO or DEBUG)
3. Verify logs in Vercel dashboard under correct deployment
4. Check function logs specifically (not just build logs)

### Need historical logs?
- Vercel keeps logs for limited time (depends on plan)
- Use log aggregation service for long-term storage
- Export logs periodically using Vercel API

## Alternative: Database Logging
For critical events, consider logging to database:
```python
# Create a LogEntry model
class LogEntry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20)
    message = models.TextField()
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    
# Then query via Django admin or custom view
```
