import os
from decouple import config, Csv
from dj_database_url import parse as dburl
from .configs import DEFAULT_DATABASE_URL, DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT, EMAIL_USE_TLS

APP_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(APP_ROOT))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

GOOGLE_DRIVE_FILE_ID = config('GOOGLE_DRIVE_FILE_ID', default='1fVEXE8Uv5BoUGO32uY4iFpOasSiIxrXS')
_LOCAL_GOOGLE_CREDENTIALS = 'H:/Lumina/secrets/google-sheets-service-account.json'
GOOGLE_DRIVE_CREDENTIALS_FILE = config(
    'GOOGLE_DRIVE_CREDENTIALS_FILE',
    default=_LOCAL_GOOGLE_CREDENTIALS if os.path.exists(_LOCAL_GOOGLE_CREDENTIALS) else '',
)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=[], cast=Csv())

# Django 4.0+ valida o header Origin em requests POST mesmo same-origin.
# Sob proxy reverso (nginx) e portas nao-default e necessario listar as
# origens explicitamente. Veja:
# https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Database: PostgreSQL em produção (Railway/Render), SQLite em desenvolvimento
# Em produção, a variável DATABASE_URL é automaticamente fornecida
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Produção: usa PostgreSQL via DATABASE_URL
    DATABASES = {
        # conn_max_age reaproveita a conexao entre requisicoes
        'default': dburl(DATABASE_URL, conn_max_age=600, conn_health_checks=True)
    }
else:
    # Desenvolvimento: usa SQLite local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(APP_ROOT, 'db.sqlite3'),
        }
    }


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Autenticacao social (Google OAuth 2.0)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # djangosige apps:
    'djangosige.apps.base',
    'djangosige.apps.login',
    'djangosige.apps.cadastro',
    'djangosige.apps.vendas',
    'djangosige.apps.compras',
    'djangosige.apps.fiscal',
    'djangosige.apps.financeiro',
    'djangosige.apps.estoque',
    
    # Led Gerencial v7.5 - Novos módulos gerenciais
    'djangosige.apps.gerencial',
    'djangosige.apps.financeiro_grupo',
    'djangosige.apps.juridico',
    'djangosige.apps.importacao',
    
    # HG Contabilidade - Sistema completo de contabilidade
    'djangosige.apps.contabilidade',

    # Documentos anexados a qualquer registro
    'djangosige.apps.anexos',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve arquivos estáticos em produção
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware para paginas que exigem login
    'djangosige.middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'djangosige.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(APP_ROOT, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # contexto para a versao do sige
                'djangosige.apps.base.context_version.sige_version',
                # contexto para a foto de perfil do usuario
                'djangosige.apps.login.context_user.foto_usuario',
                # contador de alertas do agente administrativo
                'djangosige.apps.base.context_alertas.alertas_agente',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangosige.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'pt-br'

#TIME_ZONE = 'UTC'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')  # Arquivos coletados para produção

STATICFILES_DIRS = [
    os.path.join(APP_ROOT, 'static'),
]

# WhiteNoise - compressão e cache de arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

FIXTURE_DIRS = [
    os.path.join(APP_ROOT, 'fixtures'),
]

MEDIA_ROOT = os.path.join(APP_ROOT, 'media/')
MEDIA_URL = 'media/'

# Documentos financeiros e de importacao: fora de MEDIA_ROOT, abertos apenas pelas telas do sistema
DOCUMENTOS_PRIVADOS_ROOT = os.path.join(APP_ROOT, 'documentos_privados/')

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOGIN_NOT_REQUIRED = (
    r'^/login/$',
    r'/login/esqueceu/',
    r'/login/trocarsenha/',
    r'/logout/',
    r'^/accounts/',
)

AUTHENTICATION_BACKENDS = [
    # Preserva o login atual por usuario e senha.
    'django.contrib.auth.backends.ModelBackend',
    # Habilita o login social gerenciado pelo django-allauth.
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = 'login:loginview'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'

# O Google e apenas uma forma adicional de autenticar usuarios ja cadastrados.
# Nao permite criacao publica de contas pelo fluxo social.
ACCOUNT_SIGNUP_ENABLED = False
SOCIALACCOUNT_ADAPTER = 'djangosige.apps.login.adapters.ExistingUserSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_STORE_TOKENS = False

GOOGLE_OAUTH_CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID', default='')
GOOGLE_OAUTH_CLIENT_SECRET = config('GOOGLE_OAUTH_CLIENT_SECRET', default='')
GOOGLE_LOGIN_ENABLED = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

_GOOGLE_PROVIDER = {
    'SCOPE': ['profile', 'email'],
    'AUTH_PARAMS': {
        'access_type': 'online',
        'prompt': 'select_account',
    },
    'OAUTH_PKCE_ENABLED': True,
    # So associa a um usuario local quando o Google confirmar o e-mail.
    'EMAIL_AUTHENTICATION': True,
}

if GOOGLE_LOGIN_ENABLED:
    _GOOGLE_PROVIDER['APP'] = {
        'client_id': GOOGLE_OAUTH_CLIENT_ID,
        'secret': GOOGLE_OAUTH_CLIENT_SECRET,
        'key': '',
    }

SOCIALACCOUNT_PROVIDERS = {
    'google': _GOOGLE_PROVIDER,
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# FIX STATIC FILES
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
