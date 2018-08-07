try:
    from shared_settings import *
except ImportError:
    pass


# Database_aa
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

ALLOWED_HOSTS = ['104.236.19.140', '127.0.0.1', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'production',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "pk_test_Lm0dlbotXJBWyVYWvihRWKqE")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_D6YRXHUNtl19JjqbtZD9f0aQ")