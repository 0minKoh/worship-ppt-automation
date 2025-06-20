from pathlib import Path
import os # os 모듈 임포트

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-2c%)e9ld6awm!om7)k=y1))@q2%ywbffsqi^0g%2#5e80(sgsw"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


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
        "DIRS": [],
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
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'worship_ppt_db',        # 생성할 데이터베이스 이름
        'USER': 'worship_ppt_app_user',          # PostgreSQL 사용자 이름 (예: postgres)
        'PASSWORD': 'worship_app_ymkoh',  # PostgreSQL 사용자 비밀번호
        'HOST': 'localhost',             # 데이터베이스 호스트 (로컬이면 localhost)
        'PORT': '5432',                  # PostgreSQL 포트
    }
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Redis 서버 주소 (로컬)
CELERY_RESULT_BACKEND = 'django-db'             # Celery 작업 결과를 Django DB에 저장
CELERY_ACCEPT_CONTENT = ['json']                # JSON 형식의 콘텐츠만 허용
CELERY_TASK_SERIALIZER = 'json'                 # 태스크 직렬화 방식
CELERY_RESULT_SERIALIZER = 'json'               # 결과 직렬화 방식
CELERY_TIMEZONE = 'Asia/Seoul'                  # 시간대 설정 (필요에 따라 변경)
CELERY_TASK_TRACK_STARTED = True                # 태스크가 시작되었을 때 상태 추적


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
