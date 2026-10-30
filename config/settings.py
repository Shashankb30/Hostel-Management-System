"""Django settings for the Hostel Management System foundation."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-change-me-before-deployment')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') if h.strip()]
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'students.apps.StudentsConfig',
    'rooms.apps.RoomsConfig',
    'allocation.apps.AllocationConfig',
    'attendance.apps.AttendanceConfig',
    'complaints.apps.ComplaintsConfig',
    'fees.apps.FeesConfig',
    'visitors.apps.VisitorsConfig',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.NoStoreForAuthenticatedMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True, 'OPTIONS': {'context_processors': [
        'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'core.context_processors.navigation',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {
    'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
    'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
    **({'USER': os.environ.get('DB_USER', ''), 'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''), 'PORT': os.environ.get('DB_PORT', '')}
       if os.environ.get('DB_ENGINE') == 'django.db.backends.postgresql' else {}),
}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'login'

# Show Django "error" messages as Bootstrap red alerts (shared validation framework, #13).
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

# FR-01.11: lock an account after this many wrong passwords in a row (Issue #26).
HMS_MAX_FAILED_LOGINS = int(os.environ.get('HMS_MAX_FAILED_LOGINS', '5'))

# FR-01.07: a session lasts while the user keeps working, and ends after this many idle
# minutes or when the browser closes (Issue #22).
HMS_SESSION_TIMEOUT_MINUTES = int(os.environ.get('HMS_SESSION_TIMEOUT_MINUTES', '30'))
SESSION_COOKIE_AGE = HMS_SESSION_TIMEOUT_MINUTES * 60
SESSION_SAVE_EVERY_REQUEST = True  # every request restarts the idle timer
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Lax'

# FR-01.09: password reset emails. Development prints them in the terminal; set
# EMAIL_BACKEND and the EMAIL_* variables in .env to send real mail.
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '25'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '0') == '1'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Hostel Management System <noreply@hms.local>')
# A reset link works for this many minutes.
PASSWORD_RESET_TIMEOUT = int(os.environ.get('HMS_RESET_LINK_MINUTES', '60')) * 60
