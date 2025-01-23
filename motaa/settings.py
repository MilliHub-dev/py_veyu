import os
from pathlib import Path
from environ import Env
from decouple import config
from datetime import timedelta
from dotenv import load_dotenv
import environ

env = environ.Env()
environ.Env.read_env()

load_dotenv(override=True)
# Devs can use the production settings for staging by setting the PRODUCTION environment variable to True
if os.getenv('PRODUCTION') == 'True':
    from production.settings import *
else:
    # from development.settings import *

    load_dotenv(override=True)
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent



    env = Env()
    Env.read_env(BASE_DIR / '.env')

    SECRET_KEY = env.get_value('DJANGO_SECRET_KEY')

    DEBUG = env.bool("DEBUG", False)

    if DEBUG:
        ALLOWED_HOSTS = ['*']
    else:
        ALLOWED_HOSTS = [
                'motaadev.pythonanywhere.com',
                'motaa.vercel.app',
                'motaa.com.ng',
                '*', # remove after dev testing of frontend
                ]


    # Application definition

    INSTALLED_APPS = [
            'daphne',
            # 'unfold',
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            # 'jet',
            'jazzmin',

            # Motaa Apps
            'accounts',
            'bookings',
            'chat',
            'utils',
            'feedback',
            'listings',
            'wallet',


            # Third Party Apps
            'rest_framework',
            'dj_rest_auth',
            'rest_framework.authtoken',
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

    ROOT_URLCONF = 'motaa.urls'

    TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                        # 'django.template.context_processors.request',
                        ],
                    },
                },
            ]

    WSGI_APPLICATION = 'motaa.wsgi.application'

    ASGI_APPLICATION = "motaa.asgi.application"


    # Database
    # https://docs.djangoproject.com/en/5.1/ref/settings/#databases

    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'local.db.sqlite3',
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

    STATIC_URL = 'static/'
    if DEBUG:
        STATICFILES_DIRS = [
                BASE_DIR / 'static'
                ]
    else:
        STATIC_ROOT = BASE_DIR / 'static'

    MEDIA_URL = 'media/'
    MEDIA_ROOT = BASE_DIR / 'uploads'

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
    'show_ui_builder':True,
    "custom_links" : {
        "books":[{
            "name": "Dashboard",
            "custom_links": 'analytics-dashboard',
            "icon": "fas fa-chart-line"
        }]
    }
}