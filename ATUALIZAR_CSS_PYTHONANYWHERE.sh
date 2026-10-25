#!/bin/bash
# ATUALIZAR PYTHONANYWHERE COM NOVO CSS DO LOGIN

echo "=========================================="
echo "  ATUALIZANDO CSS DO LOGIN"
echo "=========================================="
echo ""

cd ~/djangoSIGE

echo "[1/2] Baixando atualizações do GitHub..."
git pull origin main

echo ""
echo "[2/2] Verificando arquivo atualizado..."
ls -lh djangosige/templates/login/login.html

echo ""
echo "=========================================="
echo "  ✅ ARQUIVO ATUALIZADO!"
echo "=========================================="
echo ""
echo "PRÓXIMO PASSO:"
echo "Vá em Web → Reload para ativar!"
echo ""
echo "https://www.pythonanywhere.com/user/eduvazjr/webapps/"
echo ""
