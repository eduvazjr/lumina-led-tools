import os
import sys

# === ADICIONAR VIRTUALENV ===
# Ativar o virtualenv
virtualenv_path = '/home/eduvazjr/djangoSIGE/venv/lib/python3.10/site-packages'
if virtualenv_path not in sys.path:
    sys.path.insert(0, virtualenv_path)

# Adicionar o diretório do projeto ao path
path = '/home/eduvazjr/djangoSIGE'
if path not in sys.path:
    sys.path.append(path)

# Configurar variável de ambiente do Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangosige.configs.settings'

# Importar aplicação WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
