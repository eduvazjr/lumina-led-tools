#!/bin/bash
# SCRIPT 1 - FAZER UPLOAD DO PROJETO
# Cole este script no console Bash do PythonAnywhere

echo "=========================================="
echo "  DEPLOY AUTOMÁTICO - PARTE 1"
echo "=========================================="
echo ""

cd ~

# Clonar o projeto do GitHub
echo "[1/4] Clonando projeto do GitHub..."
git clone https://github.com/eduvazjr/lumina-led-tools.git djangoSIGE
cd djangoSIGE

echo ""
echo "[2/4] Instalando dependências..."
pip3 install --user -r requirements.txt

echo ""
echo "[3/4] Configurando variáveis de ambiente..."
cat > .env << 'EOF'
SECRET_KEY=qm0_t^rrrg!9f5hkk7u@we^u$3(4#i7io@88_1atm6i*49k2=f
DEBUG=False
ALLOWED_HOSTS=eduvazjr.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://eduvazjr.pythonanywhere.com
EOF

echo ""
echo "[4/4] Configurando banco de dados..."
python3 manage.py migrate
python3 manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "  ✅ PARTE 1 CONCLUÍDA!"
echo "=========================================="
echo ""
echo "Agora execute o SCRIPT 2 para criar o web app!"
echo ""
