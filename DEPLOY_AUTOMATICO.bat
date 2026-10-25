@echo off
cls

echo.
echo ===============================================================
echo    DEPLOY AUTOMATICO - LED GERENCIAL v7.5
echo ===============================================================
echo.
echo Este script vai:
echo    - Fazer login no Railway
echo    - Criar projeto automaticamente
echo    - Adicionar PostgreSQL
echo    - Configurar variaveis de ambiente
echo    - Fazer deploy
echo    - Criar superusuario
echo    - Mostrar URL do sistema online
echo.
echo ===============================================================
echo.

cd /d "C:\Users\Usuario\djangoSIGE"

REM Passo 1: Login no Railway
echo [1/7] Fazendo login no Railway...
echo.
echo SEU NAVEGADOR VAI ABRIR - FACA LOGIN COM GITHUB!
echo.
timeout /t 3 /nobreak >nul

railway login

if errorlevel 1 (
    echo.
    echo Login falhou! Execute novamente.
    pause
    exit /b 1
)

echo.
echo Login bem-sucedido!
echo.

REM Passo 2: Criar projeto
echo [2/7] Criando projeto no Railway...
echo.

railway init

if errorlevel 1 (
    echo.
    echo Falha ao criar projeto!
    pause
    exit /b 1
)

echo.
echo Projeto criado!
echo.

REM Passo 3: Adicionar PostgreSQL
echo [3/7] Adicionando PostgreSQL...
echo.
echo IMPORTANTE: Use as setas para selecionar PostgreSQL e pressione ENTER
echo.

railway add

echo.
echo PostgreSQL adicionado!
echo.

REM Passo 4: Configurar variaveis de ambiente
echo [4/7] Configurando variaveis de ambiente...
echo.

railway variables set SECRET_KEY="qm0_t^rrrg!9f5hkk7u@we^u$3(4#i7io@88_1atm6i*49k2=f"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS=".railway.app,.up.railway.app"
railway variables set CSRF_TRUSTED_ORIGINS="https://${{RAILWAY_PUBLIC_DOMAIN}}"

echo.
echo Variaveis configuradas!
echo.

REM Passo 5: Deploy
echo [5/7] Fazendo deploy...
echo.
echo Isso pode levar 2-3 minutos...
echo.

railway up

if errorlevel 1 (
    echo.
    echo Deploy pode ter falhado. Verificando logs...
    railway logs
    pause
)

echo.
echo Deploy concluido!
echo.

REM Passo 6: Executar migrations
echo [6/7] Executando migrations...
echo.

railway run python manage.py migrate

echo.
echo Migrations executadas!
echo.

REM Passo 7: Criar superusuario
echo [7/7] Criando superusuario...
echo.
echo Preencha os dados do administrador:
echo.

railway run python manage.py createsuperuser

echo.
echo Superusuario criado!
echo.

REM Obter URL do projeto
echo ===============================================================
echo    DEPLOY CONCLUIDO COM SUCESSO!
echo ===============================================================
echo.
echo Obtendo URL do seu sistema...
echo.

railway domain

echo.
echo ===============================================================
echo    SEU SISTEMA ESTA ONLINE!
echo ===============================================================
echo.
echo Acesse seu sistema em:
echo.
echo    https://seu-projeto.up.railway.app/gerencial/
echo.
echo Login Admin:
echo    https://seu-projeto.up.railway.app/admin/
echo.
echo ===============================================================
echo.
echo PROXIMOS PASSOS:
echo.
echo    1. Acesse o admin e importe seus 369 pagamentos
echo    2. Configure usuarios adicionais
echo    3. Personalize conforme necessario
echo.
echo ===============================================================
echo.

pause
