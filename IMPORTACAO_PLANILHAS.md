# 📋 MODELO DE IMPORTAÇÃO - CONTROLE GERENCIAL

## 📊 Formato CSV (delimitador: ponto-e-vírgula)

### Colunas obrigatórias:

1. **fornecedor_cnpj** ou **fornecedor_nome**: CNPJ ou nome do fornecedor (deve estar cadastrado)
2. **descricao**: Descrição do pagamento
3. **valor**: Valor em formato numérico (use ponto como separador decimal: 1500.00)
4. **data_emissao**: Data de emissão no formato DD/MM/AAAA
5. **data_vencimento**: Data de vencimento no formato DD/MM/AAAA
6. **observacoes**: Observações adicionais (opcional)

### Exemplo CSV:

```csv
fornecedor_cnpj;descricao;valor;data_emissao;data_vencimento;observacoes
12.345.678/0001-90;Compra de materiais;1500.00;21/10/2026;30/10/2026;Pedido 001
ACME LTDA;Serviços;2300.50;21/10/2026;05/11/2026;Urgente
```

---

## 📑 Formato Excel (.xlsx ou .xls)

### Colunas (nesta ordem):

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| **Fornecedor (CNPJ ou Nome)** | **Descrição** | **Valor** | **Data Emissão** | **Data Vencimento** | **Observações** |
| 12.345.678/0001-90 | Compra de materiais | 1500.00 | 21/10/2026 | 30/10/2026 | Pedido 001 |
| ACME LTDA | Serviços de manutenção | 2300.50 | 21/10/2026 | 05/11/2026 | Urgente |

**IMPORTANTE:**
- A primeira linha (cabeçalho) será ignorada
- As datas podem ser formatadas como data no Excel ou texto no formato DD/MM/AAAA
- O fornecedor deve estar previamente cadastrado no sistema
- O sistema buscará o fornecedor por CNPJ (total ou parcial) ou nome

---

## ✅ COMO USAR:

1. Acesse **Gestão Avançada → Controle Gerencial**
2. Role até o final da página
3. Clique em **"Escolher arquivo"** na seção "Importar Planilha"
4. Selecione seu arquivo (.csv, .xlsx ou .xls)
5. Clique em **"Importar"**
6. Aguarde a confirmação

---

## 📁 ARQUIVOS DE EXEMPLO:

- **modelo_importacao_pagamentos.csv** - Modelo CSV pronto para uso
- **modelo_importacao_pagamentos.xlsx** - Modelo Excel (será criado)

---

## ⚠️ OBSERVAÇÕES:

- Fornecedores não encontrados gerarão erro (mas não interrompem a importação)
- Erros de formato de data ou valor também geram erro
- Um log completo da importação é salvo no banco de dados
- Mensagens de sucesso/erro aparecerão no topo da página

---

## 🔧 SOLUÇÃO DE PROBLEMAS:

**Erro: "Biblioteca openpyxl não instalada"**
```bash
pip install openpyxl
```

**Erro: "Fornecedor não encontrado"**
- Cadastre o fornecedor primeiro em **Cadastros → Fornecedores**
- Ou use o CNPJ/nome exato de um fornecedor já cadastrado

**Erro: "Formato de data inválido"**
- Use sempre DD/MM/AAAA (exemplo: 21/10/2026)
- No Excel, formate a célula como "Texto" antes de digitar

---

**💡 Led Gerencial v7.5 - LED TOOLS**
