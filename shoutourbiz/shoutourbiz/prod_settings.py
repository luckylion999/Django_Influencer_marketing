import os

try:
    from shared_settings import *
except ImportError:
    pass

DEBUG = False
ALLOWED_HOSTS = ['shoutour.biz', '104.236.19.140', '127.0.0.1', 'localhost']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        }
    },
    'handlers': {
        'django_logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, '../logs/django_logfile'),
            'maxBytes': 1024 * 1024 * 20,
            'formatter': 'verbose',
        },
        'debug_logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, '../logs/debug_logfile'),
            'maxBytes': 1024 * 1024 * 20,
            'formatter': 'verbose',

        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['django_logfile'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'level': 'INFO',
            'handlers': ['django_logfile'],
            'propagate': False,
        },
        'main': {
            'level': 'INFO',
            'handlers': ['debug_logfile'],
            'propagate': False
        }
    }
}

FORCE_SCRIPT_NAME = '/panel'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = []
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'main', 'media')

LOGIN_URL = FORCE_SCRIPT_NAME + '/login/'

# Database connection wait time
CONN_MAX_AGE = 80

STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
