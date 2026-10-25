#!/bin/bash
# ATUALIZAR LOGIN PREMIUM NO PYTHONANYWHERE

echo "=========================================="
echo "  ATUALIZANDO LOGIN PREMIUM"
echo "=========================================="
echo ""

cd ~/djangoSIGE

echo "[1/2] Baixando novo design do GitHub..."
git pull origin main

echo ""
echo "[2/2] Verificando arquivo..."
ls -lh djangosige/templates/login/login.html

echo ""
echo "=========================================="
echo "  ✅ ATUALIZAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "PRÓXIMO PASSO:"
echo "Vá em Web → Reload para ativar!"
echo ""
echo "https://www.pythonanywhere.com/user/eduvazjr/webapps/"
echo ""
echo "Depois acesse:"
echo "https://eduvazjr.pythonanywhere.com/login/"
echo ""
