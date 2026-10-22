# 🚀 DEPLOY AGORA - INSTRUÇÕES RÁPIDAS

## ⚡ OPÇÃO RÁPIDA: RAILWAY (RECOMENDADO)

### **1. ENVIAR PARA GITHUB**
```bash
cd C:\Users\Usuario\djangoSIGE
git add .
git commit -m "Deploy: Railway/Render ready + WhiteNoise + PostgreSQL"
git push origin main
```

### **2. CRIAR CONTA RAILWAY**
👉 https://railway.app
- Login com GitHub
- Autorize o acesso

### **3. DEPLOY EM 3 CLIQUES**
1. **"+ New Project"** → **"Deploy from GitHub repo"** → Selecione `djangoSIGE`
2. **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. **"Variables"** → Adicione:
   ```
   SECRET_KEY=cole-a-chave-gerada-abaixo
   DEBUG=False
   ALLOWED_HOSTS=.railway.app
   CSRF_TRUSTED_ORIGINS=https://seu-projeto.railway.app
   ```

**Gerar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### **4. AGUARDAR DEPLOY (2-3 min)**
Acompanhe os logs na aba "Deployments"

### **5. CRIAR ADMIN**
```bash
# Instalar Railway CLI (opcional)
npm i -g @railway/cli
railway login
railway link
railway run python manage.py createsuperuser
```

**✅ PRONTO! Seu sistema estará em:**
```
https://seu-projeto.railway.app/gerencial/
```

---

## 🆓 OPÇÃO GRATUITA 100%: RENDER

### **1. ENVIAR PARA GITHUB**
```bash
git add .
git commit -m "Deploy ready"
git push origin main
```

### **2. CRIAR CONTA RENDER**
👉 https://render.com
- Login com GitHub

### **3. CRIAR WEB SERVICE**
1. **"+ New"** → **"Web Service"**
2. Conecte `djangoSIGE`
3. Configure:
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command:** `gunicorn djangosige.configs.wsgi:application`
   - **Instance Type:** Free

### **4. CRIAR POSTGRESQL**
1. **"+ New"** → **"PostgreSQL"**
2. Instance Type: Free
3. Copie a **Internal Database URL**

### **5. VARIÁVEIS DE AMBIENTE**
No Web Service → Environment:
```
SECRET_KEY=gere-aqui
DEBUG=False
DATABASE_URL=cole-internal-database-url
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://seu-projeto.onrender.com
```

### **6. CRIAR ADMIN**
No Render → Shell:
```bash
python manage.py createsuperuser
```

**✅ PRONTO! Sistema em:**
```
https://seu-projeto.onrender.com/gerencial/
```

⚠️ **Render Free:** Sleep após 15min (primeiro acesso demora ~30s)

---

## 📊 COMPARAÇÃO RÁPIDA

| Recurso | Railway | Render |
|---------|---------|--------|
| **Custo** | $5 crédito/mês | 100% grátis |
| **Sleep** | ❌ Não | ✅ Sim (15min) |
| **PostgreSQL** | Permanente | 90 dias |
| **Setup** | Mais fácil | Médio |
| **Performance** | Melhor | Boa |
| **Recomendado para** | Produção | Demonstração |

---

## 🎯 ESCOLHA SEU CAMINHO

### **Para uso real (clientes/equipe):**
👉 **RAILWAY** - Deploy em 5 minutos, sem sleep

### **Para demonstração/portfólio:**
👉 **RENDER** - 100% gratuito, funciona bem

---

## 📚 GUIAS COMPLETOS

- **Railway:** Leia `DEPLOY_RAILWAY.md` (passo a passo detalhado)
- **Render:** Leia `DEPLOY_RENDER.md` (passo a passo detalhado)

---

## ✅ CHECKLIST PRÉ-DEPLOY

Tudo pronto:
- [x] `railway.json` criado
- [x] `Procfile` criado
- [x] `runtime.txt` criado
- [x] `requirements.txt` atualizado (gunicorn, psycopg2, whitenoise)
- [x] `settings.py` configurado (WhiteNoise, PostgreSQL, STATIC_ROOT)
- [x] Banco SQLite local intacto (369 pagamentos)
- [x] Design profissional sem cara de IA

**⏭️ PRÓXIMO PASSO: GIT PUSH!**

```bash
cd C:\Users\Usuario\djangoSIGE
git add .
git commit -m "Ready for production deploy"
git push origin main
```

Depois escolha Railway ou Render e siga o guia! 🚀
