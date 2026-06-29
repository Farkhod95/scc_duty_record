import os
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from corsheaders.defaults import default_headers
import environ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env("SECRET_KEY")

DEBUG = env.bool("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost"])

INSTALLED_APPS = [
    # Modeltranslation
    'modeltranslation',

    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'channels',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    'django_celery_results',
    'django_celery_beat',

    # Local apps
    'users.apps.UsersConfig',
    'directory',
    'monitoring.apps.MonitoringConfig',
    'restapp',
    'fleet',
    'tablet',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'restapp.middlewares.simple_404.SimpleNotFoundMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # for front
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # test uchun o'chirilgan
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'restapp.middlewares.middlewares.RequestMiddleware',
    "restapp.middlewares.middlewares.CurrentUserMiddleware",
    'django.middleware.locale.LocaleMiddleware',  # for translation
]

CORS_ORIGIN_ALLOW_ALL = True

# CORS_ALLOWED_ORIGINS = [
#     "http://192.168.168.24:3033",
#     "http://192.168.168.24",
#     "http://192.168.168.24:8080",
#     "http://10.190.66.2:8081",
#     "http://localhost:3000",  # agar lokalda ishlayotgan bo‘lsa
#     "http://localhost:5173",  # agar lokalda ishlayotgan bo‘lsa
# ]


ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR + '/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'staticfiles': 'django.templatetags.static',
            }
        },
    },
]


DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

# WSGI_APPLICATION = 'main.wsgi.application'
ASGI_APPLICATION = 'main.asgi.application'

CELERY_RESULT_BACKEND = 'django-db'

CELERY_CACHE_BACKEND = 'default'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

### Local Host uchun

# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('127.0.0.1', 6379)],  # Make sure Redis is running on this port
#         },
#     },
# }
#
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://localhost:6379/1',
#     }
# }
#
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
#
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': env("DB_NAME"),
#         'USER': env("DB_USER"),
#         'PASSWORD': env("DB_PASSWORD"),
#         'HOST': env("DB_HOST"),
#         'PORT': env("DB_PORT"),
#     }
# }

### Server uchun

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env("REDIS_URL", default="redis://redis:6379/1"),
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env("SERVER_DB_NAME"),
        'USER': env("SERVER_DB_USER"),
        'PASSWORD': env("SERVER_DB_PASSWORD"),
        'HOST': env("SERVER_DB_HOST"),
        'PORT': env("SERVER_DB_PORT"),
    }
}

# Password validation

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

# Django REST framework simplejwt

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ),
    'UNICODE_JSON': True,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'EXCEPTION_HANDLER': 'restapp.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=220),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'BLACKLIST_AFTER_ROTATION': True,
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic'
        }
    },
}

LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'

LANGUAGES = (
    ('uz', _('O‘zbek (Lotin)')),
    ('uz-cyrl', _('Ўзбек (Кирилл)')),
    ('ru', _('Русский')),
    ('kaa', _('Qaraqalpaqsha')),
)

# Internationalization

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGE_CODE = 'uz'

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static")
# ]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# WhiteNoise’ga tavsiya etiladigan storage:
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

AUTH_USER_MODEL = 'users.User'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# media fayllar (upload qilingan rasm, fayl, video)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tashqi tizim integratsiyasi
# Duty approve bo'lganda shu URL ga POST yuboriladi.
# Bo'sh qoldirilsa yuborilmaydi.
EXTERNAL_DUTY_SYNC_URL = env('EXTERNAL_DUTY_SYNC_URL', default='')
EXTERNAL_SYNC_TOKEN = env('EXTERNAL_SYNC_TOKEN', default='')

# Monitoring mikroservisi (Docker network ichida)
MICROSERVICE_LOCATION_SYNC_URL   = env('MICROSERVICE_LOCATION_SYNC_URL', default='')
MICROSERVICE_POINT_SYNC_URL      = env('MICROSERVICE_POINT_SYNC_URL', default='')
MICROSERVICE_SECTION_STARTED_URL = env('MICROSERVICE_SECTION_STARTED_URL', default='')
MICROSERVICE_SECTION_ENDED_URL   = env('MICROSERVICE_SECTION_ENDED_URL', default='')
# Planshet GPS → mikroservis (location.update eventi)
LOCATION_MICROSERVICE_URL        = env('LOCATION_MICROSERVICE_URL', default='')
# Planshet GPS yuborish intervali (soniya), default 30s
TABLET_LOCATION_INTERVAL         = env.int('TABLET_LOCATION_INTERVAL', default=30)

# LocationService gRPC (Go mikroservis)
GRPC_LOCATION_SERVICE_ADDR = env('GRPC_LOCATION_SERVICE_ADDR', default='192.168.168.18:50051')

# 112 hodisa tizimi
INCIDENT_112_API_KEY        = env('INCIDENT_112_API_KEY', default='')
INCIDENT_NOTIFY_RADIUS_KM   = env.float('INCIDENT_NOTIFY_RADIUS_KM', default=3.0)

# Planshet RSA-OAEP autentifikatsiyasi
# Kalit juftini yaratish: python manage.py generate_tablet_keys
TABLET_RSA_PRIVATE_KEY = env('TABLET_RSA_PRIVATE_KEY', default='').replace('\\n', '\n')