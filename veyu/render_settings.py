"""
Render-optimized Django settings for production deployment.
Inherits from main settings and applies Render-specific optimizations.
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

# Override settings for Render production environment
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Render provides DATABASE_URL automatically for PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
    logger.info("Database configured from Render DATABASE_URL")
else:
    logger.warning("DATABASE_URL not found - using default database config")

# Render-specific allowed hosts
ALLOWED_HOSTS = [
    '.onrender.com',
    'veyu-backend.onrender.com',
    'veyu-h18m.onrender.com',
    'dev.veyu.autos',
    '.veyu.autos',
    'veyu.autos',
    'localhost',
    '127.0.0.1',
]

# Add custom domain if provided
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    ALLOWED_HOSTS.append(f'www.{CUSTOM_DOMAIN}')

# Static files configuration for Render
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

# CORS settings for Render deployment - Override environment variables
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://www.veyu.autos",
    "https://veyu.autos",
    "https://dev.veyu.autos",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# CSRF trusted origins for Render deployment - Override environment variables
CSRF_TRUSTED_ORIGINS = [
    'https://dev.veyu.autos',
    'https://veyu.autos',
    'https://www.veyu.autos',
    'http://localhost:5173',
    'http://localhost:3000',
    'http://localhost:8000',
]

if CUSTOM_DOMAIN:
    CSRF_TRUSTED_ORIGINS += [
        f"https://{CUSTOM_DOMAIN}",
        f"https://www.{CUSTOM_DOMAIN}",
    ]

# Logging configuration optimized for Render
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'render': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'render',
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

# Cache configuration for Render (use Redis if available)
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

# Email configuration for Render
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)

# Email timeout settings for Render
EMAIL_TIMEOUT = 30  # 30 seconds timeout
EMAIL_USE_TLS = True
EMAIL_PORT = 587

# Cloudinary configuration for Render
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

# Render-specific optimizations
if os.environ.get('RENDER'):
    logger.info("Running on Render platform")
    
    # Optimize for Render's environment
    CONN_MAX_AGE = 600  # Keep database connections alive
    
    # Trust Render's proxy headers
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

logger.info("Render settings configuration complete")
