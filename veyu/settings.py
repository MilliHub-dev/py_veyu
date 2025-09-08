import os
from pathlib import Path
from environ import Env
from decouple import config
from datetime import timedelta
from dotenv import load_dotenv

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


# Application definition

INSTALLED_APPS = [

    # Motaa Apps
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
]

SITE_ID = 1


AUTH_USER_MODEL = 'accounts.Account'
SMS_API_KEY = env.get_value('AFRICAS_TALKING_API_KEY')

MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',

        # Motaa Middleware
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
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'local.db.sqlite3',
            # 'NAME': BASE_DIR / 'olddb.sqlite3',
            }
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


# STORAGE SETTINGS

AWS_ACCESS_KEY_ID = 'your-spaces-access-key'
AWS_SECRET_ACCESS_KEY = 'your-spaces-secret-access-key'
AWS_STORAGE_BUCKET_NAME = 'your-storage-bucket-name'
AWS_S3_ENDPOINT_URL = 'https://nyc3.digitaloceanspaces.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'assets'


AWS_S3_SIGNATURE_VERSION = 's3v4'

MEDIA_URL = 'media/'
STATIC_URL = 'static/'

if DEBUG:
    MEDIA_URL = f'uploads/'
    STATICFILES_DIRS = [
        BASE_DIR / 'static'
    ]
else:
    STATIC_ROOT = BASE_DIR / 'static'
    STATIC_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_LOCATION}/'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    PUBLIC_MEDIA_LOCATION = 'uploads'
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{PUBLIC_MEDIA_LOCATION}/'
MEDIA_ROOT = BASE_DIR / 'uploads'


if not DEBUG:
    DEFAULT_STORAGE_BACKEND = 'veyu.storage.UploadedFileStorage'




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


# EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env.get_value('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.get_value('EMAIL_HOST_PASSWORD')

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
        'listings.Vehicle',
        'listings.VehicleImage',
        'listings.VehicleCategories',
        'listings.VehicleTags',
        'listings.PurchaseOffers',
    ],
    "order_with_respect_to": ["auth", "listings.Listing"],
    "custom_links": {
    },
}

