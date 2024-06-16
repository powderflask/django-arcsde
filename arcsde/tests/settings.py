"""
Django settings for testing document_catalogue.
"""

from pathlib import Path
import os

# Build paths inside the test suite like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build a path for temporary files
TMP_DIR = '/tmp/django-arcsde_tests/'
Path(TMP_DIR).mkdir(parents=True, exist_ok=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'foobar'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'arcsde',
    'arcsde.tests',  # define test models
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'arcsde.tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(TMP_DIR, 'db.sqlite3'),
        'TEST': {
            'MIGRATE' : False   # Django 3.1+ -- disable migrations, create test DB schema directly from models.
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Pacific'

USE_I18N = False

USE_TZ = False  # ArcSDE date/times are stored without timezone info in UTC.  Doesn't play nice with Django TZ logic
