#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar e aplicar migrations do Led Gerencial v7.5
"""
import os
import sys
import subprocess

def run_command(cmd, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print('='*60)
    print(f"\nComando: {cmd}\n")
    
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\n❌ ERRO ao executar: {description}")
        return False
    
    print(f"\n✅ {description} - CONCLUÍDO!")
    return True

def main():
    print("\n" + "="*60)
    print("  💡 LED GERENCIAL V7.5 - CRIAR MIGRATIONS")
    print("="*60)
    
    # Verificar se estamos na pasta correta
    if not os.path.exists('manage.py'):
        print("\n❌ ERRO: Este script deve ser executado na pasta do projeto!")
        print("   Pasta atual:", os.getcwd())
        print("\n   Execute:")
        print("   cd C:\\Users\\Usuario\\djangoSIGE")
        print("   python criar_migrations.py")
        return
    
    print("\n✅ Pasta correta encontrada!")
    print(f"   {os.getcwd()}")
    
    # Lista de comandos
    commands = [
        ("python manage.py makemigrations gerencial", 
         "Criando migrations do módulo GERENCIAL"),
        
        ("python manage.py makemigrations financeiro_grupo", 
         "Criando migrations do módulo FINANCEIRO GRUPO"),
        
        ("python manage.py makemigrations juridico", 
         "Criando migrations do módulo JURÍDICO"),
        
        ("python manage.py migrate", 
         "Aplicando TODAS as migrations ao banco SQLite"),
    ]
    
    # Executar comandos
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
        else:
            print(f"\n⚠️  Continuando mesmo com erro...")
    
    # Resultado final
    print("\n" + "="*60)
    print("  🎉 PROCESSO FINALIZADO!")
    print("="*60)
    print(f"\n✅ {success_count}/{len(commands)} comandos executados com sucesso")
    
    if success_count == len(commands):
        print("\n🚀 TUDO PRONTO!")
        print("\nAgora você pode:")
        print("  1. Iniciar o servidor: python manage.py runserver 0.0.0.0:8000")
        print("  2. Acessar: http://localhost:8000/gerencial/")
        print("  3. Login: admin / admin123")
    else:
        print("\n⚠️  Alguns comandos falharam.")
        print("   Verifique os erros acima.")
    
    print("\n" + "="*60)
    input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    main()
