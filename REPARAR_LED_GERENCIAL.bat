@echo off
chcp 65001 > nul
echo.
echo ═══════════════════════════════════════════════════════════
echo    🔧 LED GERENCIAL V7.5 - REINSTALAR/REPARAR
echo ═══════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo Esta ferramenta vai:
echo   1. Reinstalar Django e dependências
echo   2. Recriar as migrations
echo   3. Aplicar ao banco de dados
echo.
echo ⚠️  ATENÇÃO: Isso pode RESETAR as migrations!
echo.
pause

echo.
echo 📦 Reinstalando dependências...
echo.
pip install --upgrade django python-decouple dj-database-url

echo.
echo 🗑️  Removendo migrations antigas...
echo.
if exist "djangosige\apps\gerencial\migrations" (
    rd /s /q "djangosige\apps\gerencial\migrations"
    mkdir "djangosige\apps\gerencial\migrations"
    echo. > "djangosige\apps\gerencial\migrations\__init__.py"
)

if exist "djangosige\apps\financeiro_grupo\migrations" (
    rd /s /q "djangosige\apps\financeiro_grupo\migrations"
    mkdir "djangosige\apps\financeiro_grupo\migrations"
    echo. > "djangosige\apps\financeiro_grupo\migrations\__init__.py"
)

if exist "djangosige\apps\juridico\migrations" (
    rd /s /q "djangosige\apps\juridico\migrations"
    mkdir "djangosige\apps\juridico\migrations"
    echo. > "djangosige\apps\juridico\migrations\__init__.py"
)

echo.
echo 📋 Recriando migrations...
echo.
python manage.py makemigrations gerencial
python manage.py makemigrations financeiro_grupo
python manage.py makemigrations juridico

echo.
echo 🗄️  Aplicando migrations...
echo.
python manage.py migrate

echo.
echo ✅ REPARO COMPLETO!
echo.
pause
