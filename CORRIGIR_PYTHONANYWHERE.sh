#!/bin/bash
# SCRIPT DE CORREÇÃO - CRIAR VIRTUALENV E INSTALAR DEPENDÊNCIAS

echo "=========================================="
echo "  CORRIGINDO ERRO DE DEPENDÊNCIAS"
echo "=========================================="
echo ""

cd ~

echo "[1/6] Criando virtualenv..."
python3 -m venv djangoSIGE/venv

echo ""
echo "[2/6] Ativando virtualenv..."
source djangoSIGE/venv/bin/activate

echo ""
echo "[3/6] Atualizando pip..."
pip install --upgrade pip

echo ""
echo "[4/6] Instalando dependências..."
cd djangoSIGE
pip install -r requirements.txt

echo ""
echo "[5/6] Criando arquivo .env..."
cat > .env << 'EOF'
SECRET_KEY=qm0_t^rrrg!9f5hkk7u@we^u$3(4#i7io@88_1atm6i*49k2=f
DEBUG=False
ALLOWED_HOSTS=eduvazjr.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://eduvazjr.pythonanywhere.com
EOF

echo ""
echo "[6/6] Executando migrations..."
python manage.py migrate

echo ""
echo "=========================================="
echo "  ✅ CORREÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "PRÓXIMO PASSO:"
echo "Atualizar arquivo WSGI para usar virtualenv!"
echo ""
echo "Vá em Web → WSGI configuration file"
echo "E adicione estas linhas ANTES de 'import os':"
echo ""
echo "# Ativar virtualenv"
echo "import sys"
echo "path = '/home/eduvazjr/djangoSIGE/venv'"
echo "if path not in sys.path:"
echo "    sys.path.insert(0, path)"
echo ""
echo "activate_this = '/home/eduvazjr/djangoSIGE/venv/bin/activate_this.py'"
echo "with open(activate_this) as f:"
echo "    exec(f.read(), {'__file__': activate_this})"
echo ""
