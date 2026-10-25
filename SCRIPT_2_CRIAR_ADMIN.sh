#!/bin/bash
# SCRIPT 2 - CRIAR SUPERUSUÁRIO
# Cole este script no console Bash do PythonAnywhere

echo "=========================================="
echo "  DEPLOY AUTOMÁTICO - PARTE 2"
echo "=========================================="
echo ""

cd ~/djangoSIGE

echo "Vamos criar o superusuário do sistema!"
echo ""
echo "Digite as informações do administrador:"
echo ""

python3 manage.py createsuperuser

echo ""
echo "=========================================="
echo "  ✅ ADMIN CRIADO COM SUCESSO!"
echo "=========================================="
echo ""
echo "Agora siga as instruções para criar o Web App!"
echo ""
