#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportar dados do banco SQLite para JSON
Não depende do Django - usa sqlite3 puro
"""

import sqlite3
import json
import sys

# Conectar ao banco
db_path = 'F:/djangoSIGE/djangosige/db.sqlite3'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
cursor = conn.cursor()

print("Exportando dados do banco...")
print(f"Banco: {db_path}")
print("")

# Exportar Fornecedores
print("[1/2] Exportando fornecedores...")
cursor.execute("SELECT * FROM gerencial_fornecedor")
fornecedores = []
for row in cursor.fetchall():
    fornecedores.append({
        "model": "gerencial.fornecedor",
        "pk": row['id'],
        "fields": {
            "nome": row['nome'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }
    })
print(f"✅ {len(fornecedores)} fornecedores exportados")

# Exportar Pagamentos
print("[2/2] Exportando pagamentos...")
cursor.execute("SELECT * FROM gerencial_pagamentofornecedor")
pagamentos = []
for row in cursor.fetchall():
    pagamentos.append({
        "model": "gerencial.pagamentofornecedor",
        "pk": row['id'],
        "fields": {
            "fornecedor_id": row['fornecedor_id'],
            "data_vencimento": row['data_vencimento'],
            "valor": str(row['valor']),
            "descricao": row['descricao'],
            "status": row['status'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }
    })
print(f"✅ {len(pagamentos)} pagamentos exportados")

# Combinar e salvar
dados = fornecedores + pagamentos

output_file = 'F:/djangoSIGE/dados_exportacao.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(dados, f, indent=2, ensure_ascii=False)

print("")
print(f"✅ Arquivo criado: {output_file}")
print(f"📊 Total de registros: {len(dados)}")
print("")

conn.close()
