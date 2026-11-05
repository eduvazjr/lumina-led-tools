#!/bin/bash
# Publica no PythonAnywhere: Contas a Pagar (documentos, status, alertas) e o modulo Importacao.
# Rodar em um console Bash do PythonAnywhere:  bash PUBLICAR_PYTHONANYWHERE.sh
# Para no primeiro erro. Antes de alterar o banco, faz uma copia dele.
set -e

PROJETO=/home/eduvazjr/djangoSIGE
BRANCH=main
cd "$PROJETO"
[ -f venv/bin/activate ] && source venv/bin/activate

echo "== 1/6 Conferindo arquivos locais =="
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    git status --short --untracked-files=no
    echo "PARE: ha arquivos editados direto no servidor. Revise antes de atualizar."
    exit 1
fi

echo "== 2/6 Copia de seguranca =="
PASTA="$HOME/backup-antes-publicacao-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$PASTA"
[ -f djangosige/db.sqlite3 ] && cp -p djangosige/db.sqlite3 "$PASTA/"
git rev-parse HEAD > "$PASTA/commit-anterior.txt"
for arquivo in $(git ls-files --others --exclude-standard -i | grep 'migrations/.*\.py$' | grep -v __init__ || true); do
    mkdir -p "$PASTA/$(dirname "$arquivo")"
    cp -p "$arquivo" "$PASTA/$arquivo"
done
echo "Copia em $PASTA"

echo "== 3/6 Migracoes ja aplicadas no servidor =="
python manage.py showmigrations compras estoque financeiro vendas | tee "$PASTA/migracoes-antes.txt"

echo "== 4/6 Atualizando o codigo =="
git fetch origin
git pull --ff-only origin "$BRANCH"

echo "== 5/6 Conferindo e aplicando migracoes =="
python manage.py check
python manage.py migrate --plan
python manage.py migrate

echo "== 6/6 Pronto =="
echo "Falta recarregar o site: aba Web > botao verde Reload."
echo "Depois teste /financeiro/contapagar/listacontapagar/ e /comex/"
echo "Para desfazer: restaure o banco de $PASTA e volte o codigo para o commit em commit-anterior.txt"
