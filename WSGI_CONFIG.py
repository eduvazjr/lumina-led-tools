# WSGI Configuration File para PythonAnywhere
# Cole este conteúdo no arquivo WSGI do PythonAnywhere

import os
import sys

# Adicionar o diretório do projeto ao path
path = '/home/eduvazjr/djangoSIGE'
if path not in sys.path:
    sys.path.append(path)

# Configurar variável de ambiente do Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangosige.configs.settings'

# Importar aplicação WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
