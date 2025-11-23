"""
Vercel-optimized Django settings for serverless deployment.
Inherits from main settings and applies serverless-specific optimizations.
"""

import os
import sys
import logging

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

# Override settings for Vercel serverless environment
DEBUG = False

# Override SECRET_KEY with better error handling
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    logger.error("DJANGO_SECRET_KEY environment variable is not set!")
    raise ValueError("DJANGO_SECRET_KEY must be set in Vercel environment variables")

# Remove WebSocket/ASGI apps that aren't compatible with serverless
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in ['daphne', 'channels']]

# Vercel-specific allowed hosts
ALLOWED_HOSTS = [
    '.vercel.app',
    'veyu.vercel.app', 
    'veyu.cc',
    'dev.veyu.cc',
    '127.0.0.1',
    'localhost',
]

# Database optimization for serverless
# Force connection close after each request to prevent connection pooling issues
DATABASES['default']['CONN_MAX_AGE'] = 0
DATABASES['default']['CONN_HEALTH_CHECKS'] = True

# Add connection timeout for better error handling
if 'OPTIONS' not in DATABASES['default']:
    DATABASES['default']['OPTIONS'] = {}

DATABASES['default']['OPTIONS'].update({
    'connect_timeout': 10,
    'read_timeout': 10,
    'write_timeout': 10,
})

# Static files optimization for Vercel CDN
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure static files directories
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if os.path.exists(BASE_DIR / 'static') else []

# Static files storage with WhiteNoise for Vercel
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Static files finders for development and build
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files configuration for Vercel (use Cloudinary for uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'staticfiles', 'media')

# Validate SECRET_KEY is set (already done above, but double-check)
if not SECRET_KEY or SECRET_KEY == 'unsafe-secret-key-change-in-production':
    logger.error("Invalid or default SECRET_KEY detected!")
    raise ValueError("DJANGO_SECRET_KEY must be set to a secure value")

# Database URL override for Vercel environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,  # Critical for serverless
            conn_health_checks=True,
        )
        logger.info("Database configured from DATABASE_URL")
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}", exc_info=True)
        raise
else:
    logger.error("DATABASE_URL environment variable is not set!")
    raise ValueError("DATABASE_URL must be set in Vercel environment variables")

# Email configuration for Vercel
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session and cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# CORS settings for Vercel deployment
CORS_ALLOWED_ORIGINS = [
    "https://veyu.vercel.app",
    "https://veyu.cc",
    "https://dev.veyu.cc",
]

CORS_ALLOW_CREDENTIALS = True

# Logging configuration optimized for Vercel
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'vercel': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'vercel',
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

# Cache configuration for serverless (use dummy cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable channels for serverless (WebSocket not supported)
CHANNEL_LAYERS = {}

# Remove ASGI application for serverless
ASGI_APPLICATION = None

# Optimize middleware for serverless
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.UserTypeMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Cloudinary configuration from environment for serverless
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
if CLOUDINARY_URL:
    # Parse CLOUDINARY_URL and configure for serverless environment
    from urllib.parse import urlparse
    parsed = urlparse(CLOUDINARY_URL)
    
    if '@' in parsed.netloc:
        api_key, api_secret = parsed.netloc.split('@')[0].split(':')
        cloud_name = parsed.netloc.split('@')[-1]
        
        # Enhanced Cloudinary storage configuration for Vercel
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': cloud_name,
            'API_KEY': api_key,
            'API_SECRET': api_secret,
            'SECURE': True,
            'API_PROXY': None,  # Direct API calls for serverless
            'TIMEOUT': 30,  # Increased timeout for serverless functions
        }
        
        # Configure Cloudinary SDK for serverless environment
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
            api_proxy=None,  # No proxy for serverless
            timeout=30,  # Timeout for API calls
        )
        
        # Use Cloudinary for media file storage
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
        
        # CORS configuration for Cloudinary uploads
        CLOUDINARY_CORS_ORIGINS = [
            "https://veyu.vercel.app",
            "https://veyu.cc", 
            "https://dev.veyu.cc",
        ]
        
        # File upload configuration for serverless
        FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB max file size
        DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB max request size
        FILE_UPLOAD_PERMISSIONS = 0o644
        
        # Cloudinary upload presets for different file types
        CLOUDINARY_UPLOAD_PRESETS = {
            'profile_images': 'veyu_profile_images',
            'vehicle_images': 'veyu_vehicle_images', 
            'inspection_images': 'veyu_inspection_images',
            'documents': 'veyu_documents',
        }
        
else:
    # Fallback configuration if CLOUDINARY_URL is not set
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("CLOUDINARY_URL not configured - media uploads will not work")
    
    # Use local storage as fallback (not recommended for production)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# WhiteNoise configuration for static files serving
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False  # Disable in production for performance
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

# WhiteNoise caching configuration for Vercel CDN
WHITENOISE_MAX_AGE = 31536000  # 1 year for static files with hashed names
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: True  # All files are immutable with manifest

# Additional static file optimization
WHITENOISE_MANIFEST_STRICT = False  # Allow missing files in development
WHITENOISE_INDEX_FILE = True  # Serve index.html for directory requests

# Static file serving optimization for Vercel
# Ensure proper MIME types for static files
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.svg': 'image/svg+xml',
}

# Configure static file compression
WHITENOISE_STATIC_PREFIX = '/static/'