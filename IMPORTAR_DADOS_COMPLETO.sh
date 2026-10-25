#!/bin/bash
# SCRIPT AUTOMÁTICO - IMPORTAR 369 PAGAMENTOS
# Cole este script no console Bash do PythonAnywhere

echo "=========================================="
echo "  IMPORTANDO 369 PAGAMENTOS + 6 FORNECEDORES"
echo "=========================================="
echo ""

cd ~/djangoSIGE

echo "[1/5] Baixando dados atualizados do GitHub..."
git pull origin main

echo ""
echo "[2/5] Verificando arquivo de dados..."
if [ -f "dados_exportacao.json" ]; then
    echo "✅ Arquivo encontrado! ($(du -h dados_exportacao.json | cut -f1))"
else
    echo "❌ Arquivo não encontrado!"
    exit 1
fi

echo ""
echo "[3/5] Limpando dados antigos..."
python3 manage.py shell << 'EOF'
from djangosige.apps.gerencial.models import PagamentoFornecedor
from djangosige.apps.cadastro.models import Fornecedor, Pessoa
print(f"Antes: {PagamentoFornecedor.objects.count()} pagamentos")
PagamentoFornecedor.objects.all().delete()
print("✅ Pagamentos limpos!")
EOF

echo ""
echo "[4/5] Importando 381 registros (6 pessoas + 6 fornecedores + 369 pagamentos)..."
python3 manage.py loaddata dados_exportacao.json

echo ""
echo "[5/5] Verificando importação..."
python3 manage.py shell << 'EOF'
from djangosige.apps.gerencial.models import PagamentoFornecedor
from djangosige.apps.cadastro.models import Fornecedor
print(f"✅ Total de pagamentos: {PagamentoFornecedor.objects.count()}")
print(f"✅ Total de fornecedores: {Fornecedor.objects.count()}")

# Mostrar alguns fornecedores
print("\n📊 Fornecedores:")
for f in Fornecedor.objects.all():
    qtd = PagamentoFornecedor.objects.filter(fornecedor=f).count()
    print(f"  - {f.nome_razao_social}: {qtd} pagamentos")
EOF

echo ""
echo "=========================================="
echo "  ✅ IMPORTAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "Acesse: https://eduvazjr.pythonanywhere.com/gerencial/"
echo ""
echo "Depois vá em Web → Reload para ativar!"
echo ""
