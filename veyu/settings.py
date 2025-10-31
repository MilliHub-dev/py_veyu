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

# Use secure cookies in production
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


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
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',

        # veyu Middleware
        'utils.middleware.UserTypeMiddleware',

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
            conn_max_age=600,
            ssl_require=ssl_required,
        )
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

if DEBUG:
    MEDIA_URL = '/uploads/'
    STATICFILES_DIRS = [
        BASE_DIR / 'static'
    ]
else:
    STATIC_ROOT = BASE_DIR / 'static'
    # Keep static served via collected static; media via Cloudinary
MEDIA_ROOT = BASE_DIR / 'uploads'

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
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
            'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
            'dj_rest_auth.jwt_auth.JWTAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            ]
        }

OLD_PASSWORD_FIELD_ENABLED = True

REST_AUTH = {

    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'my-app-auth',
    'JWT_AUTH_REFRESH_COOKIE': 'my-refresh-token',

}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('DJANGO_SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'Authorization',
    # 'AUTH_HEADER_NAME': 'Authorization',


    # copied
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',


    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# from corsheaders.conf import


CORS_ALLOW_ALL_ORIGINS = True


# EMAIL CONFIGURATION
if DEBUG:
    # In development, print emails to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_FILE_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')
    DEFAULT_FROM_EMAIL = 'noreply@veyu.local'
    SERVER_EMAIL = 'noreply@veyu.local'
else:
    # Production SMTP settings
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env.get_value('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = env.get_value('EMAIL_PORT', 587)
    EMAIL_USE_TLS = env.get_value('EMAIL_USE_TLS', True)
    EMAIL_HOST_USER = env.get_value('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = env.get_value('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = env.get_value('DEFAULT_FROM_EMAIL', 'Veyu <support@veyu.cc>')
    SERVER_EMAIL = env.get_value('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
    
    # Timeout for SMTP connection (in seconds)
    EMAIL_TIMEOUT = 10  # 10 seconds timeout
    
    # Additional SMTP settings for reliability
    EMAIL_USE_SSL = env.get_value('EMAIL_USE_SSL', False)
    EMAIL_SSL_KEYFILE = env.get_value('EMAIL_SSL_KEYFILE', None)
    EMAIL_SSL_CERTFILE = env.get_value('EMAIL_SSL_CERTFILE', None)

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

