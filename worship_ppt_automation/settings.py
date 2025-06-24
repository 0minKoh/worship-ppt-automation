from pathlib import Path
import os
from dotenv import load_dotenv # dotenv 임포트

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드: 프로젝트 루트 디렉토리에 있는 .env 파일을 찾습니다.
# load_dotenv() 함수는 기본적으로 .env 파일을 찾지만, 명시적으로 경로를 지정해주는 것이 좋습니다.
load_dotenv(os.path.join(BASE_DIR, '.env'))


# SECRET_KEY
# 환경 변수가 설정되지 않은 경우를 대비하여 기본값을 지정하거나 오류를 발생시킬 수 있습니다.
# 프로덕션에서는 반드시 환경 변수로 설정해야 합니다.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-fallback-secret-key-for-dev")

# DEBUG 모드
# 문자열 'True'/'False'를 부울 값으로 변환합니다. 기본값은 False로 안전하게 설정.
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == 'true'

# ALLOWED_HOSTS
# 쉼표로 구분된 문자열을 리스트로 변환합니다.
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(',') if os.environ.get("DJANGO_ALLOWED_HOSTS") else []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "django_celery_results"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "worship_ppt_automation.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "worship_ppt_automation.wsgi.application"


# Database
# PostgreSQL 설정을 환경 변수에서 가져옵니다.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DB_NAME", "worship_ppt_db"),
        'USER': os.environ.get("DB_USER", "worship_ppt_app_user"),
        'PASSWORD': os.environ.get("DB_PASSWORD", "your_secure_password_for_worship_app"),
        'HOST': os.environ.get("DB_HOST", "localhost"),
        'PORT': os.environ.get("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ko-kr" # 한국어 설정
TIME_ZONE = "Asia/Seoul" # 한국 시간대 설정

USE_I18N = True
USE_TZ = True


# Celery Configuration
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul' # Celery 시간대도 일관성 있게 설정
CELERY_TASK_TRACK_STARTED = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Media files (User-uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Login / Logout URLs
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Gemini API Key (이미 os.environ.get으로 잘 되어 있습니다)
# utils/llm.py에서 settings.GEMINI_API_KEY를 참조합니다.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # 실제 키는 .env 파일에