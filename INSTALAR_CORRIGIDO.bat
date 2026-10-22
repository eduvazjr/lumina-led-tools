@echo off
chcp 65001 > nul
echo.
echo ═══════════════════════════════════════════════════════════
echo    💡 LED GERENCIAL V7.5 - INSTALAÇÃO CORRIGIDA  
echo ═══════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo 🔧 PASSO 0: Removendo variável DATABASE_URL do sistema...
echo.
echo    ⚠️  Esta variável estava forçando PostgreSQL!
echo.
setx DATABASE_URL "" >nul 2>&1
set DATABASE_URL=
echo ✅ Variável removida! Agora usará SQLite.
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo 📦 PASSO 1: Instalando Django e dependências...
echo ═══════════════════════════════════════════════════════════
echo.
python -m pip install --user django python-decouple dj-database-url
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: Falha ao instalar dependências!
    pause
    exit /b 1
)

echo.
echo ✅ Django instalado!
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo 📋 PASSO 2: Criando migrations...
echo ═══════════════════════════════════════════════════════════
echo.

python manage.py makemigrations gerencial financeiro_grupo juridico
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar migrations
    pause
    exit /b 1
)

echo.
echo ✅ Migrations criadas!
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo 🗄️  PASSO 3: Aplicando ao banco SQLite...
echo ═══════════════════════════════════════════════════════════
echo.

python manage.py migrate
if %errorlevel% neq 0 (
    echo ❌ Erro ao aplicar migrations
    pause
    exit /b 1
)

echo.
echo ✅ Banco SQLite atualizado!
echo.
timeout /t 2 > nul

echo ═══════════════════════════════════════════════════════════
echo    🎉 INSTALAÇÃO COMPLETA!
echo ═══════════════════════════════════════════════════════════
echo.
echo ✅ SQLite configurado (djangosige\db.sqlite3)
echo ✅ 3 módulos criados: Gerencial, Financeiro-Grupo, Jurídico
echo.
echo 🚀 INICIANDO SERVIDOR...
echo.
echo URL: http://localhost:8000
echo Login: admin / admin123
echo.
echo Pressione Ctrl+C para parar
echo.
timeout /t 3 > nul

python manage.py runserver 0.0.0.0:8000

pause
