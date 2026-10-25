#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Instalação - HG Contabilidade
Instala e configura o sistema completo de contabilidade
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(command, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"   ✅ {description} concluído!")
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Erro: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False

def main():
    print_header("HG CONTABILIDADE - INSTALAÇÃO")
    
    # Verificar se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Erro: execute este script na pasta raiz do DjangoSIGE")
        sys.exit(1)
    
    print("📂 Diretório atual:", os.getcwd())
    
    # 1. Verificar instalação do Django
    print_header("1. Verificando Dependências")
    try:
        import django
        print(f"   ✅ Django {django.get_version()} instalado")
    except ImportError:
        print("   ⚠️  Django não encontrado")
        if input("   Deseja instalar? (s/n): ").lower() == 's':
            run_command("pip install django decouple dj-database-url", 
                       "Instalando Django e dependências")
    
    # 2. Criar migrations
    print_header("2. Criando Migrations")
    run_command("python manage.py makemigrations contabilidade", 
               "Criando migrations para contabilidade")
    
    # 3. Aplicar migrations
    print_header("3. Aplicando Migrations ao Banco de Dados")
    run_command("python manage.py migrate contabilidade", 
               "Aplicando migrations")
    
    # 4. Coletar arquivos estáticos
    print_header("4. Coletando Arquivos Estáticos")
    run_command("python manage.py collectstatic --noinput", 
               "Coletando CSS/JS")
    
    # 5. Verificar superusuário
    print_header("5. Verificando Usuário Administrador")
    print("   ℹ️  Certifique-se de ter um superusuário criado")
    print("   Execute: python manage.py createsuperuser")
    
    # 6. Resumo
    print_header("INSTALAÇÃO CONCLUÍDA")
    print("✅ Sistema HG Contabilidade instalado com sucesso!")
    print("\n📊 Próximos passos:")
    print("   1. python manage.py runserver 0.0.0.0:8000")
    print("   2. Acesse http://localhost:8000/contabilidade/")
    print("   3. Faça login com suas credenciais")
    print("   4. Clique em 'Novo Processo' para começar")
    print("\n📖 Leia CONTABILIDADE_README.md para mais informações")
    print("\n🎯 Dashboard: http://localhost:8000/contabilidade/")
    print("🔧 Admin: http://localhost:8000/admin/")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)
