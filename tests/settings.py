INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'channels',
    'tests',
]
SECRET_KEY = 'dog'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST': {'NAME': 'test_db.sqlite3'},
    }
}

MIDDLEWARE_CLASSES = []

ALLOWED_HOSTS = ['127.0.0.1']
