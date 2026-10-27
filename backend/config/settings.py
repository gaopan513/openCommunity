"""
Django settings for openCommunity project.

社区论坛系统后端配置。
开发环境使用 SQLite，生产环境切换为 PostgreSQL。
"""

import os
import warnings
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# 安全配置
# 开发环境默认宽松便于本地调试；生产环境（DJANGO_DEBUG=False）强制收紧：
# SECRET_KEY 必须显式注入，ALLOWED_HOSTS / CORS 默认不放行。
# =============================================================================

# 默认开发环境开启 DEBUG；生产须显式设置 DJANGO_DEBUG=False
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# 生产环境强制要求显式注入密钥，缺失即拒绝启动（防止默认密钥被用于伪造 JWT）
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        warnings.warn('未设置 DJANGO_SECRET_KEY，正在使用开发占位密钥，仅限本地开发使用')
        SECRET_KEY = 'django-insecure-dev-only-placeholder-do-not-use-in-production'
    else:
        raise ImproperlyConfigured(
            '生产环境必须通过 DJANGO_SECRET_KEY 环境变量配置 SECRET_KEY'
        )

# DEBUG 时放开；生产须通过 DJANGO_ALLOWED_HOSTS 传入逗号分隔的白名单，缺省为空列表（拒绝一切请求）
raw_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '*' if DEBUG else '')
ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]


# =============================================================================
# 应用注册
# =============================================================================

INSTALLED_APPS = [
    # Django 内置
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方库
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    
    # 业务模块
    'apps.users',
    'apps.merchants',
    'apps.secondhand',
    'apps.qa',
    'apps.discussion',
    'apps.housekeeping',
    'apps.admin_system',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS 必须在 CommonMiddleware 之前
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# =============================================================================
# 数据库配置
# 开发默认 SQLite；生产通过 DJANGO_DB_* 环境变量切换 PostgreSQL（见 .env.example）。
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DJANGO_DB_NAME') or (BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DJANGO_DB_USER', ''),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', ''),
        'HOST': os.environ.get('DJANGO_DB_HOST', ''),
        'PORT': os.environ.get('DJANGO_DB_PORT', ''),
    }
}


# =============================================================================
# 自定义用户模型
# =============================================================================

AUTH_USER_MODEL = 'users.User'


# =============================================================================
# 密码验证
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =============================================================================
# 国际化
# =============================================================================

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# =============================================================================
# 静态文件与媒体文件
# =============================================================================

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =============================================================================
# 默认主键类型
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# Django REST Framework 配置
# =============================================================================

REST_FRAMEWORK = {
    # 默认认证方式：JWT
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    
    # 默认权限：已认证或只读
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    
    # 默认分页器
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    
    # 默认过滤器后端
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    
    # 全局异常处理器
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
    
    # 日期时间格式
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}


# =============================================================================
# SimpleJWT 配置
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}


# =============================================================================
# CORS 跨域配置
# =============================================================================

# 开发环境允许所有来源；生产默认关闭全放行，须显式配置 DJANGO_CORS_ALLOW_ALL=True
# 或通过 DJANGO_CORS_ALLOWED_ORIGINS 提供白名单
CORS_ALLOW_ALL_ORIGINS = os.environ.get('DJANGO_CORS_ALLOW_ALL', str(DEBUG)).lower() in ('true', '1', 'yes')

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('DJANGO_CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]

CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]


# =============================================================================
# 第三方服务配置
# =============================================================================

# 微信小程序登录（wx.login code 换取 openid）；
# 两项均为空表示未启用，/auth/wechat-login/ 会返回明确错误码
WECHAT_MINIAPP_APPID = os.environ.get('WECHAT_MINIAPP_APPID', '')
WECHAT_MINIAPP_SECRET = os.environ.get('WECHAT_MINIAPP_SECRET', '')


# =============================================================================
# 文件上传限制
# =============================================================================

# 最大上传大小 10MB（单文件 5MB 在 validator 中控制）
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
