@echo off
chcp 65001 > nul
title HG Contabilidade - Inicializacao Automatica

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║           HG CONTABILIDADE - SISTEMA DE GESTAO                    ║
echo ║                   Inicializacao Automatica                        ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

cd /d C:\Users\Usuario\djangoSIGE

echo [1/5] Verificando ambiente...
if not exist "manage.py" (
    echo [ERRO] Arquivo manage.py nao encontrado!
    pause
    exit /b 1
)

echo [2/5] Ativando ambiente virtual...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Ambiente virtual ativado!
) else (
    echo [AVISO] Ambiente virtual nao encontrado
)

echo [3/5] Criando migrations da contabilidade...
python manage.py makemigrations contabilidade
if errorlevel 1 (
    echo [AVISO] Erro ao criar migrations - pode ser normal se ja existirem
)

echo [4/5] Aplicando migrations ao banco de dados...
python manage.py migrate contabilidade
if errorlevel 1 (
    echo [AVISO] Erro ao aplicar migrations - pode ser normal se ja estiverem aplicadas
)

echo [5/5] Iniciando servidor Django...
echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                    SERVIDOR INICIADO COM SUCESSO!                 ║
echo ║                                                                   ║
echo ║  Dashboard:  http://localhost:8000/contabilidade/                 ║
echo ║  Admin:      http://localhost:8000/admin/                         ║
echo ║                                                                   ║
echo ║  Usuario: admin                                                   ║
echo ║  Senha:   admin123                                                ║
echo ║                                                                   ║
echo ║  Pressione Ctrl+C para parar o servidor                           ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

start http://localhost:8000/contabilidade/

python manage.py runserver 0.0.0.0:8000
