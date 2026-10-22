# 💡 Led Gerencial v7.5 - LED TOOLS

## 🚀 INÍCIO RÁPIDO

### ✅ 4 Atalhos Criados na sua Área de Trabalho:

#### 1️⃣ **💡 Instalar Led Gerencial** ⭐ (USE ESTE PRIMEIRO)
- **Quando usar:** Primeira vez ou reinstalação
- **O que faz:** Instala Django, cria módulos, configura banco, inicia servidor
- **Tempo:** 2-3 minutos

#### 2️⃣ **🚀 Led Gerencial - Iniciar** (Uso diário)
- **Quando usar:** Após a primeira instalação
- **O que faz:** Inicia apenas o servidor Django
- **Tempo:** 5 segundos

#### 3️⃣ **🌐 Led Gerencial - Abrir** (Acesso rápido)
- **Quando usar:** Quando o servidor já está rodando
- **O que faz:** Abre http://localhost:8000 no navegador
- **Tempo:** Instantâneo

#### 4️⃣ **📁 Led Gerencial - Pasta** (Arquivos)
- **Quando usar:** Para ver/editar arquivos do projeto
- **O que faz:** Abre C:\Users\Usuario\djangoSIGE
- **Tempo:** Instantâneo

---

## 📋 COMO COMEÇAR

### Passo 1: Instalação Inicial
1. Vá até a **Área de Trabalho**
2. Dê **duplo clique** em: `💡 Instalar Led Gerencial`
3. Aguarde 2-3 minutos
4. O navegador vai abrir automaticamente!

### Passo 2: Login
- **URL:** http://localhost:8000
- **Usuário:** admin
- **Senha:** admin123

### Passo 3: Acessar Novos Módulos
No menu lateral, veja a seção **"Gestão Avançada"**:
- 💼 **Controle Gerencial** - Pagamentos a fornecedores
- 🏢 **Financeiro - Grupo** - Transferências entre empresas
- ⚖️ **Controle Jurídico** - Processos e demandas legais

---

## 💼 MÓDULOS DISPONÍVEIS

### 1. Controle Gerencial (`/gerencial/`)
**Funcionalidades:**
- Dashboard com 6 KPIs (média semanal, mensal, maior/menor dívida)
- Cadastro de pagamentos a fornecedores
- Controle de vencimentos e alertas
- Importação de planilhas Excel/CSV
- Gráficos interativos (Chart.js)

**Modelos:**
- `PagamentoFornecedor` - Controle completo de pagamentos
- `ImportacaoPlanilha` - Log de importações

---

### 2. Financeiro - Grupo (`/financeiro-grupo/`)
**Funcionalidades:**
- Dashboard com matriz de transferências
- Controle de manobras financeiras entre empresas
- CPF do proprietário do grupo
- Relatórios de fluxo consolidado
- Confirmação de transferências

**Modelos:**
- `TransferenciaGrupo` - Transferências entre empresas
- `ProprietarioGrupo` - Dados do proprietário (nome, CPF)
- `SaldoEmpresa` - Saldos atualizados por empresa

---

### 3. Controle Jurídico (`/juridico/`)
**Funcionalidades:**
- Dashboard de processos ativos
- Pesquisa em tribunais (TRF, TST, TJSP, STJ, STF)
- Controle de prazos e alertas
- Classificação de risco (Alto, Médio, Baixo)
- Avisos automáticos para diretoria
- Upload de documentos processuais

**Modelos:**
- `Processo` - Processos judiciais completos
- `Prazo` - Controle de deadlines
- `AlertaDiretoria` - Notificações de risco
- `DocumentoProcesso` - Documentos anexados

---

## 🤖 AGENTES IA ESPECIALIZADOS

3 agentes de IA foram criados como **Hermes Skills**:

### 1. **Agente Tributário** 📊
- Expertise: ICMS, ISS, PIS, COFINS, regimes tributários
- Trigger: "tributário", "fiscal", "impostos"

### 2. **Agente Financeiro** 💰
- Expertise: Fluxo de caixa, DRE, inadimplência, cobranças
- Trigger: "financeiro", "fluxo de caixa", "contas a pagar"

### 3. **Agente Jurídico** ⚖️
- Expertise: Processos, tribunais, prazos, contratos
- Trigger: "jurídico", "processo", "tribunal", "TRF", "STJ"

---

## 🛠️ SCRIPTS DISPONÍVEIS

### 📄 INSTALAR_LED_GERENCIAL.bat
- Instalação completa + início automático
- Cria migrations dos 3 novos módulos
- Aplica ao banco SQLite

### 📄 INICIAR_SERVIDOR.bat
- Apenas inicia o servidor Django
- Para uso diário (após instalação)

### 📄 REPARAR_LED_GERENCIAL.bat
- Reinstala dependências
- Recria migrations
- Corrige problemas no banco
- ⚠️ Pode apagar dados dos novos módulos!

### 📄 CRIAR_ATALHOS.vbs
- Cria os 4 atalhos na área de trabalho
- Já foi executado automaticamente

---

## 📊 ESTATÍSTICAS DO SISTEMA

### Led Gerencial v7.5
- **Templates:** 45+ (42 originais + 3 novos dashboards)
- **Módulos funcionais:** 20 (17 originais + 3 novos)
- **Novos modelos:** 9 (distribuídos em 3 apps)
- **Novas views:** 19
- **Novas rotas:** 19
- **Agentes IA:** 3 (Hermes skills)
- **Documentação:** 25+ arquivos

### Tecnologias
- **Django:** 5.2.14
- **Python:** 3.11
- **Banco:** SQLite (db.sqlite3)
- **Frontend:** HTML5, CSS3, JavaScript (Chart.js)
- **Design:** LED TOOLS (#FF9100 orange)

---

## 🎨 DESIGN SYSTEM

### Cores LED TOOLS
- **Primary:** #FF9100 (laranja)
- **Hover:** #E67E00 (laranja escuro)
- **Highlights:** #FFB84D
- **Backgrounds:** #FFF3E0
- **Text:** #0f172a

### Tipografia
- **Fonte:** -apple-system, BlinkMacSystemFont, Segoe UI
- **Estilo:** Corporativo, profissional, minimalista

---

## 📂 ESTRUTURA DO PROJETO

```
djangoSIGE/
├── djangosige/
│   ├── apps/
│   │   ├── gerencial/                  ← NOVO v7.5
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── admin.py
│   │   ├── financeiro_grupo/           ← NOVO v7.5
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── admin.py
│   │   └── juridico/                   ← NOVO v7.5
│   │       ├── models.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── admin.py
│   ├── templates/
│   │   ├── gerencial/
│   │   │   └── dashboard.html          ← NOVO v7.5
│   │   ├── financeiro_grupo/
│   │   │   └── dashboard.html          ← NOVO v7.5
│   │   └── juridico/
│   │       └── dashboard.html          ← NOVO v7.5
│   ├── configs/
│   │   └── settings.py                 (3 apps adicionados)
│   └── urls.py                         (3 rotas adicionadas)
├── .env                                (Configurado para SQLite)
├── db.sqlite3                          (Banco de dados)
├── INSTALAR_LED_GERENCIAL.bat          ← NOVO atalho
├── INICIAR_SERVIDOR.bat                ← NOVO atalho
├── REPARAR_LED_GERENCIAL.bat           ← NOVO reparo
└── COMO_USAR.html                      ← NOVO guia visual
```

---

## 🔧 TROUBLESHOOTING

### Erro: "psycopg2 or psycopg module"
✅ **Resolvido!** O arquivo `.env` foi configurado para SQLite.

### Erro: "Django not installed"
✅ Execute: `💡 Instalar Led Gerencial` na área de trabalho

### Servidor não inicia
1. Feche todas as janelas do PowerShell
2. Execute: `💡 Instalar Led Gerencial`

### Porta 8000 em uso
```bash
# Encontrar processo usando porta 8000
netstat -ano | findstr :8000

# Matar processo (substitua PID)
taskkill /PID <número> /F
```

### Resetar banco de dados
1. Feche o servidor
2. Delete: `db.sqlite3`
3. Execute: `REPARAR_LED_GERENCIAL.bat`

---

## 📚 DOCUMENTAÇÃO COMPLETA

### Arquivos de Referência
- `LED_GERENCIAL_V7.5_DOCUMENTACAO_COMPLETA.md` - Guia completo (705 linhas)
- `LED_GERENCIAL_V7.5_RESUMO_FINAL.html` - Resumo visual animado
- `LED_GERENCIAL_V7.5_NOVOS_MODULOS.html` - Detalhes técnicos
- `INSTALACAO_LED_GERENCIAL_V7.5.md` - Passo a passo instalação
- `COMO_USAR.html` - Guia visual interativo

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Dê duplo clique em: `💡 Instalar Led Gerencial`
2. ⏱️ Aguarde 2-3 minutos
3. 🌐 Acesse: http://localhost:8000
4. 🔐 Login: admin / admin123
5. 💼 Explore os 3 novos módulos em **"Gestão Avançada"**

---

## 💡 LED TOOLS - Led Gerencial v7.5

**Sistema ERP completo com módulos gerenciais e IA integrada**

Versão: 7.5  
Data: 21 de outubro de 2026  
Desenvolvido para: LED TOOLS  
Tecnologia: Django 5.2 + Python 3.11 + Hermes AI

---

🚀 **COMECE AGORA:** Abra a **Área de Trabalho** → Duplo clique em `💡 Instalar Led Gerencial`
