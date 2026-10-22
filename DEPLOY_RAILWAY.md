# 🚀 LED GERENCIAL v7.5 - DEPLOY NO RAILWAY

## 📋 PRÉ-REQUISITOS

✅ Conta no GitHub (gratuita)  
✅ Conta no Railway (gratuita - $5 crédito mensal)  
✅ Repositório Git configurado

---

## 🎯 PASSO A PASSO COMPLETO

### **1. PREPARAR REPOSITÓRIO GITHUB**

```bash
# No seu terminal/PowerShell:
cd C:\Users\Usuario\djangoSIGE

# Adicionar arquivos novos ao Git
git add .
git commit -m "Deploy: Railway config + PostgreSQL support"

# Enviar para o GitHub
git push origin main
```

---

### **2. CRIAR CONTA NO RAILWAY**

1. Acesse: https://railway.app
2. Clique em **"Start a New Project"**
3. Faça login com sua conta **GitHub**
4. Autorize o Railway a acessar seus repositórios

---

### **3. CRIAR PROJETO NO RAILWAY**

1. Na dashboard do Railway, clique **"+ New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Encontre e selecione: **`djangoSIGE`**
4. Railway vai detectar automaticamente o Django!

---

### **4. ADICIONAR POSTGRESQL**

1. No projeto criado, clique **"+ New"**
2. Selecione **"Database"** → **"Add PostgreSQL"**
3. Railway cria o banco automaticamente
4. A variável `DATABASE_URL` é configurada automaticamente ✅

---

### **5. CONFIGURAR VARIÁVEIS DE AMBIENTE**

No Railway, vá em **"Variables"** e adicione:

```bash
SECRET_KEY=gere-uma-chave-secreta-aleatoria-aqui
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app
CSRF_TRUSTED_ORIGINS=https://seu-projeto.railway.app,https://seu-projeto.up.railway.app
```

**⚠️ IMPORTANTE:**
- `SECRET_KEY`: Gere uma chave segura (50+ caracteres aleatórios)
- `DEBUG`: SEMPRE **False** em produção
- `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`: Railway preenche automaticamente o domínio

---

### **6. GERAR SECRET_KEY SEGURA**

No terminal/PowerShell:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie o resultado e cole em `SECRET_KEY` no Railway.

---

### **7. DEPLOY AUTOMÁTICO**

Railway vai:
1. ✅ Instalar dependências (`pip install -r requirements.txt`)
2. ✅ Coletar arquivos estáticos (`collectstatic`)
3. ✅ Criar tabelas do banco (`migrate`)
4. ✅ Iniciar o servidor com Gunicorn

**Acompanhe os logs** na aba "Deployments" do Railway.

---

### **8. CRIAR SUPERUSUÁRIO (ADMIN)**

Após o deploy bem-sucedido:

1. No Railway, vá em **"Settings"** → **"Environment"**
2. Copie o valor de **`DATABASE_URL`**
3. No seu terminal local:

```bash
cd C:\Users\Usuario\djangoSIGE

# Definir temporariamente DATABASE_URL
set DATABASE_URL=cole-aqui-o-valor-copiado

# Criar superusuário
python manage.py createsuperuser
```

Ou use o **Railway CLI**:

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Fazer login
railway login

# Conectar ao projeto
railway link

# Criar superusuário
railway run python manage.py createsuperuser
```

---

### **9. IMPORTAR DADOS (369 PAGAMENTOS)**

**Opção A: Via Admin Django**

1. Acesse: `https://seu-projeto.railway.app/admin`
2. Faça login com o superusuário
3. Vá em **Controle Gerencial** → **Importar Planilha**
4. Envie seu arquivo Excel

**Opção B: Via Terminal (Recomendado)**

```bash
# Copiar banco SQLite local para produção
railway run python manage.py dumpdata gerencial > dados.json
railway run python manage.py loaddata dados.json
```

---

### **10. ACESSAR O SISTEMA ONLINE**

Seu LED Gerencial estará online em:

```
https://seu-projeto.railway.app
https://seu-projeto.railway.app/gerencial/
https://seu-projeto.railway.app/admin/
```

**Railway fornece HTTPS automático!** 🔒

---

## 🔧 COMANDOS ÚTEIS

### **Ver logs em tempo real:**
```bash
railway logs
```

### **Executar comandos no servidor:**
```bash
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput
railway run python manage.py createsuperuser
```

### **Redeploy manual:**
```bash
git add .
git commit -m "Update"
git push origin main
```

Railway re-deploya automaticamente a cada push!

---

## 💰 CUSTOS RAILWAY

- ✅ **$5 de crédito grátis/mês**
- ✅ PostgreSQL gratuito (500 MB)
- ✅ Hospedagem gratuita até consumir os $5
- ✅ HTTPS incluído
- ✅ Deploy automático incluído

**Estimativa de uso:**
- Projeto pequeno/médio: **~$3-4/mês** (dentro do crédito grátis!)
- Sem cartão de crédito necessário para começar

---

## 🆘 PROBLEMAS COMUNS

### **Erro: "Application failed to respond"**
- Verifique se `Procfile` existe
- Confirme que `gunicorn` está em `requirements.txt`
- Cheque os logs: `railway logs`

### **Erro: "Bad Request (400)"**
- Adicione seu domínio Railway em `ALLOWED_HOSTS`
- Adicione em `CSRF_TRUSTED_ORIGINS` com `https://`

### **Arquivos estáticos não carregam (CSS/JS)**
- Execute: `railway run python manage.py collectstatic --noinput`
- Verifique se `whitenoise` está em `requirements.txt`

### **Banco de dados vazio**
- Execute: `railway run python manage.py migrate`
- Importe dados: use `loaddata` ou admin web

---

## 📞 SUPORTE

- **Railway Docs:** https://docs.railway.app
- **Discord Railway:** https://discord.gg/railway
- **Django Docs:** https://docs.djangoproject.com

---

## ✅ CHECKLIST FINAL

Antes de fazer deploy, confirme:

- [ ] `railway.json` criado
- [ ] `Procfile` criado
- [ ] `runtime.txt` criado (Python 3.11.9)
- [ ] `requirements.txt` com gunicorn, psycopg2-binary, whitenoise
- [ ] `settings.py` com WhiteNoise middleware
- [ ] `settings.py` com STATIC_ROOT configurado
- [ ] `settings.py` com lógica DATABASE_URL
- [ ] `.env` NÃO commitado (está em `.gitignore`)
- [ ] Código enviado para GitHub (`git push`)
- [ ] PostgreSQL adicionado no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy bem-sucedido (logs sem erro)
- [ ] Superusuário criado
- [ ] Site acessível via HTTPS

---

🎉 **PRONTO! SEU ERP ESTÁ NA NUVEM!** 🎉
