# 🚀 LED GERENCIAL v7.5 - DEPLOY NO RENDER

## 📋 PRÉ-REQUISITOS

✅ Conta no GitHub (gratuita)  
✅ Conta no Render (100% gratuita - sem cartão)  
✅ Repositório Git configurado

---

## 🎯 PASSO A PASSO COMPLETO

### **1. PREPARAR REPOSITÓRIO GITHUB**

```bash
cd C:\Users\Usuario\djangoSIGE

git add .
git commit -m "Deploy: Render config + PostgreSQL support"
git push origin main
```

---

### **2. CRIAR CONTA NO RENDER**

1. Acesse: https://render.com
2. Clique em **"Get Started"**
3. Faça login com **GitHub**
4. Autorize o Render

---

### **3. CRIAR WEB SERVICE**

1. No dashboard do Render, clique **"+ New"** → **"Web Service"**
2. Conecte seu repositório **`djangoSIGE`**
3. Configure:

**Name:** `led-gerencial` (ou o que preferir)  
**Region:** `Oregon (US West)` ou mais próximo  
**Branch:** `main`  
**Runtime:** `Python 3`  
**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command:**
```bash
gunicorn djangosige.configs.wsgi:application
```

**Instance Type:** `Free` ✅

---

### **4. CRIAR POSTGRESQL**

1. No dashboard, clique **"+ New"** → **"PostgreSQL"**
2. Configure:

**Name:** `led-gerencial-db`  
**Database:** `ledgerencial`  
**User:** `ledgerencial_user`  
**Region:** Mesmo do Web Service  
**PostgreSQL Version:** `16`  
**Instance Type:** `Free` ✅

3. Clique **"Create Database"**
4. Copie a **Internal Database URL** (formato: `postgresql://...`)

---

### **5. CONFIGURAR VARIÁVEIS DE AMBIENTE**

No **Web Service**, vá em **"Environment"** e adicione:

```bash
SECRET_KEY=gere-uma-chave-secreta-aqui
DEBUG=False
DATABASE_URL=cole-aqui-a-internal-database-url
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://led-gerencial.onrender.com
PYTHON_VERSION=3.11.9
```

**Gerar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### **6. DEPLOY**

1. Clique **"Create Web Service"**
2. Render vai:
   - ✅ Clonar seu repositório
   - ✅ Instalar dependências
   - ✅ Executar collectstatic
   - ✅ Executar migrations
   - ✅ Iniciar Gunicorn

**Acompanhe os logs!**

---

### **7. CRIAR SUPERUSUÁRIO**

Após o deploy:

1. No Web Service, vá em **"Shell"** (no menu superior)
2. Execute:

```bash
python manage.py createsuperuser
```

Ou via terminal local:

```bash
# Instalar Render CLI (opcional)
# https://render.com/docs/cli

# Ou usar SSH
ssh [seu-usuario]@ssh.onrender.com
cd /opt/render/project/src
python manage.py createsuperuser
```

---

### **8. IMPORTAR DADOS**

**Via Admin Web:**

1. Acesse: `https://led-gerencial.onrender.com/admin`
2. Faça login
3. Vá em **Controle Gerencial** → **Importar Planilha**
4. Envie seu Excel

**Via Shell (Recomendado):**

```bash
# No Shell do Render:
python manage.py dumpdata gerencial > dados.json
python manage.py loaddata dados.json
```

---

### **9. ACESSAR O SISTEMA**

```
https://led-gerencial.onrender.com
https://led-gerencial.onrender.com/gerencial/
https://led-gerencial.onrender.com/admin/
```

**HTTPS automático incluído!** 🔒

---

## ⚠️ LIMITAÇÕES DO PLANO FREE

- ⏱️ **Sleep após 15 min de inatividade** (primeiro acesso demora ~30s para "acordar")
- 💾 **PostgreSQL expira após 90 dias** (pode criar novo banco e migrar dados)
- 🚀 **750 horas/mês** (suficiente para projeto pessoal/demonstração)

**Solução para evitar sleep:**
- Use serviço de "ping" gratuito (UptimeRobot, cron-job.org)
- Ou upgrade para plano pago ($7/mês - sem sleep)

---

## 🔧 COMANDOS ÚTEIS

### **Ver logs:**
```bash
# No dashboard: "Logs" tab
# Ou via CLI:
render logs
```

### **Executar comandos:**
```bash
# No dashboard: "Shell" tab
python manage.py migrate
python manage.py collectstatic --noinput
```

### **Redeploy manual:**
```bash
# No dashboard: "Manual Deploy" → "Clear build cache & deploy"
# Ou via Git:
git push origin main  # Auto-deploya
```

---

## 💰 CUSTOS RENDER

**Plano Free:**
- ✅ **100% gratuito**
- ✅ PostgreSQL gratuito (90 dias)
- ✅ Web Service gratuito (750h/mês)
- ✅ HTTPS incluído
- ❌ Sleep após 15min inatividade
- ❌ Sem custom domain no free

**Plano Paid ($7/mês):**
- ✅ Sem sleep
- ✅ Custom domain
- ✅ PostgreSQL permanente
- ✅ Mais recursos (RAM/CPU)

---

## 🆘 PROBLEMAS COMUNS

### **Erro: "Application failed to respond"**
- Verifique `Procfile`
- Confirme `gunicorn` em `requirements.txt`
- Cheque logs

### **Erro: "Bad Request (400)"**
- Adicione `.onrender.com` em `ALLOWED_HOSTS`
- Adicione em `CSRF_TRUSTED_ORIGINS` com `https://`

### **PostgreSQL connection refused**
- Use **Internal Database URL** (não a External)
- Formato: `postgresql://user:pass@internal-host/db`

### **Arquivos estáticos 404**
- Execute: `python manage.py collectstatic --noinput`
- Verifique `whitenoise` em MIDDLEWARE

---

## ✅ CHECKLIST FINAL

- [ ] `Procfile` criado
- [ ] `runtime.txt` criado
- [ ] `requirements.txt` completo
- [ ] `settings.py` configurado
- [ ] Código no GitHub
- [ ] PostgreSQL criado
- [ ] Variáveis de ambiente setadas
- [ ] Deploy bem-sucedido
- [ ] Superusuário criado
- [ ] Site acessível

---

🎉 **SEU ERP ESTÁ ONLINE GRATUITAMENTE!** 🎉
