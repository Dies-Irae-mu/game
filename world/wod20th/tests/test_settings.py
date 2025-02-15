"""
Test settings for World of Darkness 20th Anniversary Edition tests.
"""
from evennia.settings_default import *

# Use a faster test runner
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Use an in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:'
        }
    }
}

# Disable South migrations during testing
SOUTH_TESTS_MIGRATE = False

# Disable cache during testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable celery during testing
CELERY_ALWAYS_EAGER = True

# Use faster password hasher during testing
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
) 