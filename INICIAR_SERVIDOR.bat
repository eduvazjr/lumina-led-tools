@echo off
chcp 65001 > nul
echo.
echo ═══════════════════════════════════════════════════════════
echo    🚀 LED GERENCIAL V7.5 - INICIAR SERVIDOR
echo ═══════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo Iniciando servidor Django...
echo.
echo URL: http://localhost:8000
echo Login: admin / admin123
echo.
echo Novos módulos disponíveis:
echo   • 💼 Controle Gerencial
echo   • 🏢 Financeiro - Grupo  
echo   • ⚖️ Controle Jurídico
echo.
echo Para PARAR o servidor, pressione: Ctrl + C
echo.

python manage.py runserver 0.0.0.0:8000

pause
