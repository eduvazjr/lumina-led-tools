@echo off
title HG Contabilidade

cd /d C:\Users\Usuario\djangoSIGE

echo.
echo ========================================================================
echo           HG CONTABILIDADE - Inicializando Sistema
echo ========================================================================
echo.

echo [1/4] Criando migrations...
.venv\Scripts\python.exe manage.py makemigrations contabilidade

echo [2/4] Aplicando migrations...
.venv\Scripts\python.exe manage.py migrate contabilidade

echo [3/4] Abrindo navegador...
start http://localhost:8000/contabilidade/

echo [4/4] Iniciando servidor...
echo.
echo ========================================================================
echo  SERVIDOR RODANDO!
echo.
echo  Acesse: http://localhost:8000/contabilidade/
echo  Admin:  http://localhost:8000/admin/
echo.
echo  Usuario: admin
echo  Senha:   admin123
echo.
echo  Pressione Ctrl+C para parar
echo ========================================================================
echo.

.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
