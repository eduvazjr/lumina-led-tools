#!/bin/bash
# SCRIPT AUTOMÁTICO - IMPORTAR DADOS DO GITHUB

echo "=========================================="
echo "  IMPORTANDO 369 PAGAMENTOS"
echo "=========================================="
echo ""

cd ~/djangoSIGE

echo "[1/4] Baixando dados do GitHub..."
git pull origin main

echo ""
echo "[2/4] Limpando banco de dados atual..."
python3 manage.py shell << 'PYTHON_SCRIPT'
from djangosige.apps.gerencial.models import PagamentoFornecedor, Fornecedor
PagamentoFornecedor.objects.all().delete()
Fornecedor.objects.all().delete()
print("✅ Banco limpo!")
PYTHON_SCRIPT

echo ""
echo "[3/4] Importando 369 pagamentos..."
python3 manage.py loaddata dados_exportacao.json

echo ""
echo "[4/4] Verificando importação..."
python3 manage.py shell << 'PYTHON_SCRIPT'
from djangosige.apps.gerencial.models import PagamentoFornecedor, Fornecedor
print(f"✅ Total de pagamentos: {PagamentoFornecedor.objects.count()}")
print(f"✅ Total de fornecedores: {Fornecedor.objects.count()}")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "  ✅ IMPORTAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "Acesse: https://eduvazjr.pythonanywhere.com/gerencial/"
echo ""
