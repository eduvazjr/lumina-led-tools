#!/bin/bash
# RESTAURAR VERSÃO ANTIGA - EMERGÊNCIA

echo "Restaurando template antigo..."
cd ~/djangoSIGE
cp djangosige/templates/vendas/orcamento_venda/orcamento_venda_list_old.html djangosige/templates/vendas/orcamento_venda/orcamento_venda_list.html

echo "✅ Template restaurado!"
echo "Recarregue o site agora!"
