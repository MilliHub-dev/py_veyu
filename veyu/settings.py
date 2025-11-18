import os
from pathlib import Path
from environ import Env
from decouple import config, Csv
from datetime import timedelta
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env.get_value('DJANGO_SECRET_KEY')

DEBUG = env.bool("DEBUG", False)

if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [
            'veyudev.pythonanywhere.com',
            'veyu.vercel.app',
            'veyu.com.ng',
            'veyu-backend.onrender.com',
            'api.veyu.com',
            '*', # remove after dev testing of frontend
            ]

# Trust frontend/admin origins for CSRF when behind a proxy (Render)
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.render.com',
    'https://*.veyu.cc',
    'https://veyu.com.ng',
    'https://api.veyu.com',
    'https://dev.veyu.cc',
]

# Respect X-Forwarded-Proto from Render proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Enhanced Security Settings
# =========================

# Cookie Security
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
CSRF_COOKIE_SECURE = not DEBUG     # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True     # Prevent JavaScript access
CSRF_COOKIE_HTTPONLY = True        # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF protection
CSRF_COOKIE_SAMESITE = 'Lax'       # CSRF protection

# Session Security
SESSION_COOKIE_AGE = 86400          # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS Settings (production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Password Validation Enhancement
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Account Security Settings
ACCOUNT_LOCKOUT_ENABLED = True
ACCOUNT_LOCKOUT_MAX_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION_MINUTES = 30

# Rate Limiting Settings
RATE_LIMITING_ENABLED = True
RATE_LIMIT_LOGIN_ATTEMPTS = 5      # per minute
RATE_LIMIT_SIGNUP_ATTEMPTS = 3     # per minute
RATE_LIMIT_PASSWORD_RESET = 2      # per minute
RATE_LIMIT_API_DEFAULT = 60        # per minute

# JWT Security Enhancement
JWT_AUTH_HEADER_PREFIX = 'Bearer'
JWT_ALLOW_REFRESH = True
JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=7)
JWT_AUTH_COOKIE = None  # Disable cookie-based JWT for API security


# Application definition

INSTALLED_APPS = [

    # veyu Apps
    'accounts',
    'chat',
    'bookings',
    'feedback',
    'listings',
    'wallet',
    'utils',
    'analytics',
    'docs',
    'inspections',


    'daphne',
    # 'dj_palette',
    # 'unfold',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # 'jet',



    # Third Party Apps
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django_filters',
    'corsheaders',
    'channels',
    'drf_yasg',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'cloudinary',
    'cloudinary_storage',
]

SITE_ID = 1


AUTH_USER_MODEL = 'accounts.Account'
SMS_API_KEY = env.get_value('AFRICAS_TALKING_API_KEY')

MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        
        # Security middleware (order matters)
        'accounts.middleware.SecurityHeadersMiddleware',
        'accounts.middleware.RateLimitMiddleware',
        'accounts.middleware.SecurityLoggingMiddleware',
        
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        
        # CSRF middleware with API exemption
        'accounts.middleware.CSRFExemptionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        
        # Account lockout middleware (after authentication)
        'accounts.middleware.AccountLockoutMiddleware',
        
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',

        # veyu Middleware
        'utils.middleware.CorrelationIdMiddleware',
        'utils.middleware.UserTypeMiddleware',
        'utils.middleware.GlobalExceptionMiddleware',

        # Downloaded Middleware
        'allauth.account.middleware.AccountMiddleware',
        ]

ROOT_URLCONF = 'veyu.urls'

TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [ BASE_DIR / 'templates'],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ]

WSGI_APPLICATION = 'veyu.wsgi.application'
ASGI_APPLICATION = 'veyu.asgi.application'


# Database
# Prefer DATABASE_URL (Neon/PostgreSQL); fallback to SQLite in local dev
# Force SQLite in DEBUG mode for local development (ignore DATABASE_URL if network issues)
if DEBUG:
    # Always use SQLite in DEBUG mode to avoid network issues
    DB_URL = f'sqlite:///{BASE_DIR / "local.db.sqlite3"}'
    print(f"[DEBUG MODE] Using SQLite database at: {BASE_DIR / 'local.db.sqlite3'}")
else:
    DB_URL = env('DATABASE_URL', default='')
    if not DB_URL or not str(DB_URL).strip():
        DB_URL = f'sqlite:///{BASE_DIR / "local.db.sqlite3"}'

ssl_required = False
try:
    scheme = DB_URL.split(':', 1)[0]
    if scheme in {"postgres", "postgresql", "pgsql", "redshift", "timescale", "timescalegis"} and not DEBUG:
        ssl_required = True
except Exception:
    pass

DATABASES = {
        'default': dj_database_url.parse(
            DB_URL,
            conn_max_age=0,  # Don't persist connections (better for Neon pooler)
            ssl_require=ssl_required,
            conn_health_checks=True,  # Enable connection health checks
        )
}

# Add connection options for PostgreSQL (Neon-compatible)
if 'postgres' in DB_URL and not DEBUG:
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',  # Required for Neon
        'connect_timeout': 10,
    }

# drf-yasg (Swagger) configuration
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Format: Bearer <token>'
        }
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


# Load environment variables
load_dotenv()

# Cloudinary configuration from CLOUDINARY_URL
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')

# Parse CLOUDINARY_URL
if CLOUDINARY_URL:
    from urllib.parse import urlparse
    
    # Parse the URL
    parsed = urlparse(CLOUDINARY_URL)
    
    # Extract credentials
    api_key, api_secret = parsed.netloc.split('@')[0].split(':') if '@' in parsed.netloc else (None, None)
    cloud_name = parsed.netloc.split('@')[-1] if '@' in parsed.netloc else parsed.netloc
    
    # Configure Cloudinary
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': cloud_name,
        'API_KEY': api_key,
        'API_SECRET': api_secret,
        'SECURE': True,
    }
    
    # Initialize Cloudinary
    import cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
else:
    raise ImproperlyConfigured("CLOUDINARY_URL environment variable not set")

# STORAGE SETTINGS (Cloudinary for media)
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# Use Cloudinary for media uploads
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Static files configuration
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# In production, collectstatic will collect files to STATIC_ROOT
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (user uploads)
MEDIA_ROOT = BASE_DIR / 'uploads'

# Create directories if they don't exist
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)

# WhiteNoise static files storage (fingerprinted files for caching)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'




# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST FRAMEWORK
REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': [
            'django_filters.rest_framework.DjangoFilterBackend',
            ],
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'accounts.authentication.EnhancedJWTAuthentication',  # Enhanced JWT with blacklisting
            'rest_framework.authentication.TokenAuthentication',  # Fallback for API tokens
            'rest_framework.authentication.SessionAuthentication',  # For web interface
            'rest_framework.authentication.BasicAuthentication',  # For admin/debug
            ]
        }

OLD_PASSWORD_FIELD_ENABLED = True

REST_AUTH = {

    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'my-app-auth',
    'JWT_AUTH_REFRESH_COOKIE': 'my-refresh-token',

}

SIMPLE_JWT = {
    # Token lifetimes - more secure defaults
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Shorter access token lifetime
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Longer refresh token lifetime
    'ROTATE_REFRESH_TOKENS': True,  # Enable refresh token rotation
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old refresh tokens
    'UPDATE_LAST_LOGIN': True,  # Update last login on token refresh

    # Algorithm and signing
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('DJANGO_SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'veyu-platform',

    # Header configuration
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    # Token classes and claims
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    # User identification
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    # Additional security claims
    'JTI_CLAIM': 'jti',  # JWT ID for blacklisting
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# JWT Blacklist settings
JWT_BLACKLIST_TIMEOUT = int(timedelta(days=7).total_seconds())  # Keep blacklisted tokens for 7 days

# from corsheaders.conf import


CORS_ALLOW_ALL_ORIGINS = True


# ===============================================
# ===============================================
# SIMPLE EMAIL CONFIGURATION - BREVO SMTP
# ===============================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Brevo SMTP Settings (simple and direct)
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 60  # Increased to 60 seconds for server environments

# Get credentials from environment
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '9b4e78001@smtp-brevo.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'xsmtpsib-f8430f6957c5e0272f0399b903ed8b58ff5a6a4fda60f90bb89c9b674a77f287-oEdguD5gZaC10W04')

# From email address
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@veyu.cc')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Support email address (for user contact)
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'support@veyu.cc')

# Email verification timeout
EMAIL_VERIFICATION_TIMEOUT = 3600  # 1 hour

# Email logging configuration (moved to LOGGING section below)

# Enhanced Logging configuration with structured JSON logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s',
        },
        'structured': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'formatter': 'verbose',
        },
        # Main application log
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'structured',
        },
        # Email-specific logs
        'email_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'email.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'structured',
        },
        # Authentication-specific logs
        'auth_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'auth.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'structured',
        },
        # API-specific logs
        'api_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'api.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'structured',
        },
        # Error-specific logs
        'error_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 15,
            'formatter': 'structured',
        },
        # Security-specific logs
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 10,
            'formatter': 'structured',
        },
        # Database-specific logs
        'database_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'database.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'structured',
        },
    },
    'loggers': {
        # Django core loggers
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['api_file', 'error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'api_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'error_file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['database_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.template': {
            'handlers': ['error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        
        # Email logging
        'django.core.mail': {
            'handlers': ['email_file', 'console' if DEBUG else 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'utils.mail': {
            'handlers': ['email_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'utils.zeptomail': {
            'handlers': ['email_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'accounts.utils.email_notifications': {
            'handlers': ['email_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # Authentication logging
        'accounts.api.views': {
            'handlers': ['auth_file', 'api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'accounts.models': {
            'handlers': ['auth_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'rest_framework_simplejwt': {
            'handlers': ['auth_file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # API logging
        'bookings.api': {
            'handlers': ['api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'chat.api': {
            'handlers': ['api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'feedback.api': {
            'handlers': ['api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'listings.api': {
            'handlers': ['api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'wallet.views': {
            'handlers': ['api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # Error handling logging
        'utils.error_handlers': {
            'handlers': ['error_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'utils.middleware': {
            'handlers': ['error_file', 'api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'veyu.error_handler': {
            'handlers': ['error_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'veyu.middleware': {
            'handlers': ['error_file', 'api_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # Business logic logging
        'utils.otp': {
            'handlers': ['auth_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'utils.sms': {
            'handlers': ['auth_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # Root logger for application
        'veyu': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Log email configuration
import logging
logger = logging.getLogger(__name__)
logger.info(f"Using email backend: {EMAIL_BACKEND}")
logger.info(f"Email host: {EMAIL_HOST}:{EMAIL_PORT}")
logger.info(f"Using TLS: {EMAIL_USE_TLS}")
logger.info(f"From email: {DEFAULT_FROM_EMAIL}")

# Frontend URL for email verification and password reset links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://dev.veyu.cc')

# CACHES Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# DJANGO CHANNELS
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}


JAZZMIN_SETTINGS = {
    "site_logo": 'veyu/veyu-logo-3.png',
    "site_title": "Veyu Admin",
    "site_header": "Veyu Admin Portal",
    "index_template": "admin/index.html",
    "welcome_sign": "Welcome to Veyu Admin!",
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Listings", "app": "listings", "models": ['Listing', 'Order']},  # Direct link to an app
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "listings.Listing": "fas fa-car",
    },
    "hide_models": [
        'listings.VehicleCategories',
        'listings.VehicleTags',
        'listings.PurchaseOffers',
    ],
    "order_with_respect_to": ["auth", "listings.Listing"],
    "custom_links": {
    },
}

