#!/bin/bash
# SCRIPT COMPLETO - DEPLOY PYTHONANYWHERE
# Cole TUDO de uma vez no console Bash do PythonAnywhere

echo "=========================================="
echo "  DEPLOY COMPLETO - LED GERENCIAL v7.5"
echo "=========================================="
echo ""

cd ~/djangoSIGE

echo "[1/6] Instalando pacotes faltantes..."
pip3 install --user dj-database-url python-decouple django

echo ""
echo "[2/6] Criando banco de dados..."
python3 manage.py migrate

echo ""
echo "[3/6] Coletando arquivos estáticos..."
python3 manage.py collectstatic --noinput

echo ""
echo "[4/6] Criando arquivo .env..."
cat > .env << 'EOF'
SECRET_KEY=qm0_t^rrrg!9f5hkk7u@we^u$3(4#i7io@88_1atm6i*49k2=f
DEBUG=False
ALLOWED_HOSTS=eduvazjr.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://eduvazjr.pythonanywhere.com
EOF

echo ""
echo "=========================================="
echo "  ✅ INSTALAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "PRÓXIMO PASSO:"
echo "Execute manualmente para criar o admin:"
echo ""
echo "  python3 manage.py createsuperuser"
echo ""
echo "Digite:"
echo "  Username: admin"
echo "  Email: admin@ledtools.com"
echo "  Password: (sua senha - min 8 chars)"
echo ""
echo "=========================================="
echo ""
