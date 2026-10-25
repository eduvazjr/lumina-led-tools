#!/bin/bash
# SCRIPT AUTOMÁTICO - ATUALIZAR ORÇAMENTOS PREMIUM NO PYTHONANYWHERE

echo "======================================"
echo "  INSTALANDO TEMPLATE PREMIUM"
echo "======================================"
echo ""

cd ~/djangoSIGE

echo "[1/4] Fazendo backup do template atual..."
cp djangosige/templates/vendas/orcamento_venda/orcamento_venda_list.html djangosige/templates/vendas/orcamento_venda/orcamento_venda_list_backup_$(date +%Y%m%d%H%M%S).html

echo "[2/4] Baixando versão premium do GitHub..."
git fetch origin
git checkout origin/main -- djangosige/templates/vendas/orcamento_venda/orcamento_venda_list.html 2>/dev/null || git pull origin main

echo "[3/4] Verificando arquivo..."
if [ -f "djangosige/templates/vendas/orcamento_venda/orcamento_venda_list.html" ]; then
    SIZE=$(stat -f%z "djangosige/templates/vendas/orcamento_venda/orcamento_venda_list.html" 2>/dev/null || stat -c%s "djangosige/templates/vendas/orcamento_venda/orcamento_venda_list.html")
    echo "✅ Arquivo atualizado! Tamanho: $SIZE bytes"
else
    echo "❌ Erro: Arquivo não encontrado!"
    exit 1
fi

echo ""
echo "[4/4] Testando sintaxe Django..."
python manage.py check --deploy 2>&1 | head -10

echo ""
echo "======================================"
echo "  ✅ TEMPLATE INSTALADO!"
echo "======================================"
echo ""
echo "PRÓXIMO PASSO:"
echo "Vá em Web → Reload"
echo "https://www.pythonanywhere.com/user/eduvazjr/webapps/"
echo ""
