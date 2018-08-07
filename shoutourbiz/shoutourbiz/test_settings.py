try:
    from shared_settings import *
except ImportError:
    pass

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdb.db',
    }
}

MIGRATION_MODULES = {'main': 'main.migrations_not_used_in_tests'}