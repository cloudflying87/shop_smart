import os
import sys
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Environment variable validation
def get_env_variable(var_name, default=None, required=False):
    """Get environment variable or return exception if required and not set."""
    value = os.environ.get(var_name, default)
    if required and not value:
        error_msg = f"Required environment variable '{var_name}' is not set"
        print(error_msg, file=sys.stderr)
        raise Exception(error_msg)
    return value

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable('SECRET_KEY', 'django-insecure-development-key-change-in-production', 
                             required=not get_env_variable('DEBUG', 'False') == 'True')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env_variable('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = get_env_variable('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'django_filters',
    
    # Local apps
    'shopping',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add whitenoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shop_smart.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'shop_smart.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': get_env_variable('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': get_env_variable('DB_NAME', 'shopsmart', required=not DEBUG),
        'USER': get_env_variable('DB_USER', 'postgres', required=not DEBUG),
        'PASSWORD': get_env_variable('DB_PASSWORD', 'postgres', required=not DEBUG),
        'HOST': get_env_variable('DB_HOST', 'db'),  # Use 'db' for Docker, 'localhost' for local dev
        'PORT': get_env_variable('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(get_env_variable('DB_CONN_MAX_AGE', '600')),
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

LOGIN_REDIRECT_URL = 'groceries:dashboard'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log' if os.path.exists('/app/logs') else os.path.join(BASE_DIR, 'logs/django.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'shopping': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Use Redis cache if available
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES['default'] = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
SESSION_SAVE_EVERY_REQUEST = True

# Email settings
EMAIL_BACKEND = get_env_variable('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = get_env_variable('EMAIL_HOST', '')
EMAIL_PORT = int(get_env_variable('EMAIL_PORT', '587'))
EMAIL_USE_TLS = get_env_variable('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD', '', required=not DEBUG and EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend')

# PWA settings
PWA_APP_NAME = get_env_variable('PWA_APP_NAME', 'ShopSmart')
PWA_APP_SHORT_NAME = get_env_variable('PWA_APP_SHORT_NAME', 'ShopSmart')
PWA_APP_DESCRIPTION = get_env_variable('PWA_APP_DESCRIPTION', 'Your personal grocery shopping assistant')
PWA_APP_THEME_COLOR = get_env_variable('PWA_APP_THEME_COLOR', '#4CAF50')
PWA_APP_BACKGROUND_COLOR = get_env_variable('PWA_APP_BACKGROUND_COLOR', '#FFFFFF')
PWA_APP_DISPLAY = get_env_variable('PWA_APP_DISPLAY', 'standalone')
PWA_APP_SCOPE = get_env_variable('PWA_APP_SCOPE', '/')
PWA_APP_START_URL = get_env_variable('PWA_APP_START_URL', '/')

# API Settings
OPENFOODFACTS_USER_AGENT = get_env_variable('OPENFOODFACTS_USER_AGENT', 'ShopSmart - Django Shopping App')

# Cloudflare settings
CLOUDFLARE_TUNNEL_TOKEN = get_env_variable('CLOUDFLARE_TUNNEL_TOKEN', '', required=not DEBUG)


# Security settings
if not DEBUG:
    print("Running in production mode with security settings enabled.")
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # Cloudflare proxy settings
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# CSRF trusted origins (needed for Cloudflare deployment)
CSRF_TRUSTED_ORIGINS = []
for host in ALLOWED_HOSTS:
    if host.startswith('http'):
        CSRF_TRUSTED_ORIGINS.append(host)
    else:
        CSRF_TRUSTED_ORIGINS.append(f'https://{host}')

# Authentication URLs
LOGIN_REDIRECT_URL = '/app/'
LOGOUT_REDIRECT_URL = '/'