import os
import sys

print("═══════════════════════════════════════════════════════════")
print("   🔍 DIAGNÓSTICO - LED GERENCIAL")
print("═══════════════════════════════════════════════════════════")
print()

# Verificar Python
print("📍 PYTHON:")
print(f"   Versão: {sys.version}")
print(f"   Executável: {sys.executable}")
print()

# Verificar Django
try:
    import django
    print(f"✅ Django instalado: {django.get_version()}")
except ImportError:
    print("❌ Django NÃO instalado!")
print()

# Verificar .env
print("📍 ARQUIVO .ENV:")
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"   ✅ Encontrado em: {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        db_lines = [line.strip() for line in lines if 'DATABASE' in line.upper()]
        print(f"   Linhas com DATABASE:")
        for line in db_lines:
            print(f"      {line}")
else:
    print(f"   ❌ .env NÃO encontrado em: {env_path}")
print()

# Verificar variáveis de ambiente do sistema
print("📍 VARIÁVEIS DE AMBIENTE DO SISTEMA:")
database_url = os.environ.get('DATABASE_URL')
if database_url:
    print(f"   ⚠️ DATABASE_URL definida no sistema: {database_url[:50]}...")
else:
    print(f"   ✅ DATABASE_URL não está no ambiente do sistema")
print()

# Verificar python-decouple
try:
    from decouple import config
    print("✅ python-decouple instalado")
    
    # Tentar ler DATABASE_URL do .env
    try:
        db_url = config('DATABASE_URL', default='NOT_SET')
        print(f"   DATABASE_URL do .env: {db_url}")
    except Exception as e:
        print(f"   ❌ Erro ao ler DATABASE_URL: {e}")
except ImportError:
    print("❌ python-decouple NÃO instalado!")
print()

# Verificar dj-database-url
try:
    import dj_database_url
    print("✅ dj-database-url instalado")
except ImportError:
    print("❌ dj-database-url NÃO instalado!")
print()

# Verificar configuração do Django
print("📍 CONFIGURAÇÃO DO DJANGO:")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangosige.configs.settings')
    import django
    django.setup()
    
    from django.conf import settings
    
    db_config = settings.DATABASES.get('default', {})
    engine = db_config.get('ENGINE', 'NOT_SET')
    name = db_config.get('NAME', 'NOT_SET')
    
    print(f"   ENGINE: {engine}")
    print(f"   NAME: {name}")
    
    if 'sqlite' in engine.lower():
        print("   ✅ Usando SQLite")
    elif 'postgres' in engine.lower():
        print("   ❌ Usando PostgreSQL (PROBLEMA ENCONTRADO!)")
    else:
        print(f"   ⚠️ Engine desconhecido: {engine}")
    
except Exception as e:
    print(f"   ❌ Erro ao verificar configuração Django: {e}")

print()
print("═══════════════════════════════════════════════════════════")
print("   FIM DO DIAGNÓSTICO")
print("═══════════════════════════════════════════════════════════")
