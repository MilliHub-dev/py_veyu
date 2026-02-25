"""
Railway-optimized Django settings for production deployment.
Inherits from main settings and applies Railway-specific optimizations.
"""

import os
import sys
import logging
import dj_database_url

# Configure logging first for better error visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Import base settings with error handling
try:
    from .settings import *
    logger.info("Base settings imported successfully")
except Exception as e:
    logger.error(f"Failed to import base settings: {e}", exc_info=True)
    raise

# Override settings for Railway production environment
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Railway provides DATABASE_URL automatically for PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
    logger.info("Database configured from Railway DATABASE_URL")
else:
    logger.warning("DATABASE_URL not found - using default database config")

# Railway-specific allowed hosts
ALLOWED_HOSTS = [
    '.railway.app',
    '.up.railway.app', 
    'veyu.up.railway.app',
    'dev.veyu.cc',
    'veyu.cc',
    'www.veyu.cc',
    'localhost',
    '127.0.0.1',
]

# Add custom domain if provided
RAILWAY_STATIC_URL = os.environ.get('RAILWAY_STATIC_URL')
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    ALLOWED_HOSTS.append(f'www.{CUSTOM_DOMAIN}')

# Static files configuration for Railway
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Use WhiteNoise for static files serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration (use Cloudinary for uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# CORS settings for Railway deployment
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "https://veyu.up.railway.app",
#     "https://dev.veyu.cc",
#     "https://veyu.cc",
#     "https://www.veyu.cc",
#     "http://localhost:5173",  # For local development
#     "http://localhost:3000",  # For local development
# ]

# if CUSTOM_DOMAIN:
#     CORS_ALLOWED_ORIGINS.extend([
#         f"https://{CUSTOM_DOMAIN}",
#         f"https://www.{CUSTOM_DOMAIN}",
#     ])

CORS_ALLOW_CREDENTIALS = True

# Logging configuration optimized for Railway
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'railway': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'railway',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Cache configuration for Railway (use Redis if available)
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    
    # Use Redis for sessions if available
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
    
    # Channel layers for WebSocket (if using channels)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    # Fallback to database cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }

# Email configuration for Railway
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)

# Email timeout settings for Railway
EMAIL_TIMEOUT = 30  # 30 seconds timeout
EMAIL_USE_TLS = True
EMAIL_PORT = 587

# Cloudinary configuration for Railway
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
if CLOUDINARY_URL:
    # Parse CLOUDINARY_URL and configure
    from urllib.parse import urlparse
    parsed = urlparse(CLOUDINARY_URL)
    
    if '@' in parsed.netloc:
        api_key, api_secret = parsed.netloc.split('@')[0].split(':')
        cloud_name = parsed.netloc.split('@')[-1]
        
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': cloud_name,
            'API_KEY': api_key,
            'API_SECRET': api_secret,
            'SECURE': True,
        }
        
        # Configure Cloudinary SDK
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        
        # Use Cloudinary for media file storage
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
        
        logger.info("Cloudinary configured successfully")
else:
    logger.warning("CLOUDINARY_URL not configured - media uploads will use local storage")

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0

# Railway-specific optimizations
if os.environ.get('RAILWAY_ENVIRONMENT'):
    logger.info("Running on Railway platform")
    
    # Optimize for Railway's environment
    CONN_MAX_AGE = 600  # Keep database connections alive
    
    # Trust Railway's proxy headers
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

logger.info("Railway settings configuration complete")