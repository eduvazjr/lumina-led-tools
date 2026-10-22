@echo off
chcp 65001 > nul
echo.
echo ═══════════════════════════════════════════════════════════
echo    💡 LED GERENCIAL V7.5 - INSTALAÇÃO AUTOMÁTICA
echo ═══════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo 📦 PASSO 1: Instalando Django e dependências...
echo.
pip install django python-decouple dj-database-url
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: Falha ao instalar dependências!
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Django instalado com sucesso!
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo 📋 PASSO 2: Criando migrations dos novos módulos...
echo ═══════════════════════════════════════════════════════════
echo.

echo → Criando migrations do módulo GERENCIAL...
python manage.py makemigrations gerencial
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar migrations do módulo gerencial
    pause
    exit /b 1
)

echo → Criando migrations do módulo FINANCEIRO GRUPO...
python manage.py makemigrations financeiro_grupo
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar migrations do módulo financeiro_grupo
    pause
    exit /b 1
)

echo → Criando migrations do módulo JURÍDICO...
python manage.py makemigrations juridico
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar migrations do módulo juridico
    pause
    exit /b 1
)

echo.
echo ✅ Migrations criadas com sucesso!
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo 🗄️  PASSO 3: Aplicando migrations ao banco de dados...
echo ═══════════════════════════════════════════════════════════
echo.

python manage.py migrate
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: Falha ao aplicar migrations!
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Banco de dados atualizado com sucesso!
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo    🎉 INSTALAÇÃO COMPLETA!
echo ═══════════════════════════════════════════════════════════
echo.
echo ✅ Django instalado
echo ✅ 3 novos módulos criados:
echo    • 💼 Controle Gerencial
echo    • 🏢 Financeiro - Grupo
echo    • ⚖️ Controle Jurídico
echo.
echo ✅ Banco de dados configurado (SQLite)
echo.
echo ═══════════════════════════════════════════════════════════
echo    🚀 INICIANDO SERVIDOR...
echo ═══════════════════════════════════════════════════════════
echo.
echo Servidor iniciando em: http://localhost:8000
echo.
echo Login: admin / admin123
echo.
echo Para PARAR o servidor, pressione: Ctrl + C
echo.
timeout /t 3 > nul

python manage.py runserver 0.0.0.0:8000

pause
