
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangosige.configs.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

# Executar comando de migrations
from django.core.management import call_command

print("Criando migrations para contabilidade...")
try:
    call_command('makemigrations', 'contabilidade')
    print("✓ Migrations criadas com sucesso!")
except Exception as e:
    print(f"Erro ao criar migrations: {e}")

print("\nAplicando migrations...")
try:
    call_command('migrate', 'contabilidade')
    print("✓ Migrations aplicadas com sucesso!")
except Exception as e:
    print(f"Erro ao aplicar migrations: {e}")
