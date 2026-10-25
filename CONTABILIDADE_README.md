# Sistema HG Contabilidade - Instalação e Uso

## 📋 Sistema Criado

Foi criado um **sistema completo de contabilidade** baseado no fluxo de processos HG Contabilidade com **5 módulos integrados**:

### Módulos Implementados

1. **ENTRADA DE CLIENTE**
   - Contato inicial
   - Coleta de informações
   - Análise da necessidade
   - Abertura do processo no sistema
   - Definição do escopo e equipe responsável

2. **LEGALIZAÇÃO**
   - Abertura/alteração/baixa de empresa
   - Registro na Junta Comercial (JUCEMG)
   - Inscrições municipais e estaduais
   - Alvarás e licenças
   - Cadastro em órgãos reguladores

3. **DEPARTAMENTO PESSOAL (DP)**
   - Admissões e demissões
   - Folha de pagamento
   - Férias e rescisões
   - eSocial e obrigações trabalhistas
   - Benefícios e encargos sociais

4. **FISCAL**
   - Emissão e controle de notas fiscais
   - Apuração de tributos
   - Obrigações acessórias (DAPI, SPED, etc.)
   - Monitoramento de regimes fiscais
   - Atendimento a fiscalizações

5. **CONTÁBIL**
   - Classificação e lançamentos contábeis
   - Conciliação bancária
   - Demonstrações contábeis (DRE)
   - Apuração de resultados
   - Suporte para decisões e planejamento

## 📁 Arquivos Criados

### Models (djangosige/apps/contabilidade/models.py)
- `ProcessoContabil` - Processo principal que integra todos os módulos
- `EntradaCliente` - Módulo 1
- `Legalizacao` - Módulo 2
- `DepartamentoPessoal`, `Funcionario`, `FolhaPagamento` - Módulo 3
- `Fiscal`, `ApuracaoTributos`, `ObrigacaoAcessoria` - Módulo 4
- `Contabil`, `LancamentoContabil`, `ConciliacaoBancaria`, `DemonstracaoResultado` - Módulo 5

### Views (djangosige/apps/contabilidade/views.py)
- Dashboard com fluxo de processos
- CRUD completo para todos os módulos
- Relatórios integrados

### Forms (djangosige/apps/contabilidade/forms.py)
- Formulários para todos os modelos
- Validações integradas

### Templates HTML
- `dashboard.html` - Dashboard principal com fluxo visual
- `lista_processos.html` - Listagem de processos
- `detalhe_processo.html` - Detalhes e navegação entre módulos
- `novo_processo.html` - Criação de processo
- Templates para cada módulo

### CSS/JS (djangosige/apps/contabilidade/static/contabilidade/)
- `css/contabilidade.css` - Design corporativo enterprise-grade
- `js/contabilidade.js` - Interações e animações

### Admin (djangosige/apps/contabilidade/admin.py)
- Interface administrativa para todos os modelos

### URLs (djangosige/apps/contabilidade/urls.py)
- Rotas completas para todos os módulos

## 🎨 Design

**Estilo:** Enterprise-grade corporativo
- Paleta de cores: #0f172a (azul escuro), #64748b (cinza), #FF9100 (laranja LED)
- Tipografia: System fonts
- Layout: Clean, profissional, sem gradientes ou cores vibrantes
- Responsivo e otimizado para impressão

## 🚀 Instalação

### 1. Instalar Django (se necessário)

```bash
cd C:/Users/Usuario/djangoSIGE
pip install django decouple dj-database-url
```

### 2. Criar e Aplicar Migrations

```bash
# Criar migrations
python manage.py makemigrations contabilidade

# Aplicar ao banco de dados
python manage.py migrate contabilidade
```

### 3. Criar Superusuário (se ainda não existe)

```bash
python manage.py createsuperuser
```

### 4. Coletar Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 5. Iniciar Servidor

```bash
python manage.py runserver 0.0.0.0:8000
```

## 📊 Uso

### Acessar o Sistema

1. **URL Principal:** http://localhost:8000/contabilidade/
2. **Admin:** http://localhost:8000/admin/

### Fluxo de Trabalho

1. Acesse o dashboard em `/contabilidade/`
2. Clique em "Novo Processo" para criar um processo contábil
3. Preencha os dados do cliente e número do processo
4. Navegue pelos 5 módulos sequencialmente:
   - Entrada de Cliente
   - Legalização
   - Departamento Pessoal
   - Fiscal
   - Contábil
5. O sistema rastreia automaticamente o progresso (1-5 etapas)
6. Visualize relatórios e estatísticas no dashboard

## 🗂️ Estrutura de Dados

### ProcessoContabil
- Número do processo (único)
- Cliente (FK)
- Empresa (FK, opcional)
- Status (entrada → legalização → dp → fiscal → contábil → concluído)
- Responsável e Equipe
- Datas de controle

### Relacionamentos
- 1 Processo → 1 Entrada de Cliente
- 1 Processo → 1 Legalização
- 1 Processo → 1 DP → N Funcionários → N Folhas
- 1 Processo → 1 Fiscal → N Apurações → N Obrigações
- 1 Processo → 1 Contábil → N Lançamentos → N Conciliações → N DREs

## 🔧 Configuração

O app já está configurado em:
- `djangosige/configs/settings.py` → INSTALLED_APPS
- `djangosige/urls.py` → URL patterns

## 📈 Features

✅ Dashboard visual com fluxo de 5 etapas
✅ Rastreamento de progresso automático (%)
✅ Alertas de obrigações vencendo
✅ CRUD completo para todos os módulos
✅ Interface administrativa
✅ Design corporativo enterprise
✅ Responsivo
✅ Integrado com sistema existente

## 🎯 Próximos Passos Sugeridos

1. Adicionar validações de negócio (ex: não permitir pular etapas)
2. Implementar anexo de documentos (PDFs, imagens)
3. Adicionar notificações por e-mail
4. Criar dashboard de métricas avançadas
5. Exportação de relatórios em PDF/Excel
6. Integração com APIs da Receita Federal
7. Calendário de obrigações fiscais
8. Workflow de aprovações

## 📞 Suporte

Sistema criado para **LED TOOLS / HG Contabilidade**
Data: Outubro 2026
Desenvolvido com Django 5.2.14

---

**PROCESSO INTEGRADO** 🔄
Mais agilidade • Mais segurança • Mais resultados
