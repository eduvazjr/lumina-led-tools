# 🚀 DEPLOY AUTOMÁTICO - LED GERENCIAL v7.5

## ✅ **TUDO PRONTO!**

Preparei um script que faz **TODO O DEPLOY AUTOMATICAMENTE** para você!

---

## 📋 **O QUE O SCRIPT FAZ:**

1. ✅ Faz login no Railway (abre navegador 1 vez)
2. ✅ Cria projeto automaticamente
3. ✅ Adiciona PostgreSQL
4. ✅ Configura todas as variáveis de ambiente
5. ✅ Faz deploy completo
6. ✅ Executa migrations
7. ✅ Cria superusuário (você digita usuário/senha/email)
8. ✅ Mostra URL do sistema online

**VOCÊ SÓ FAZ:**
- 1 clique para fazer login com GitHub
- Digitar dados do admin (usuário/senha/email)

**Pronto! Sistema online em ~5 minutos!** ⏱️

---

## 🎯 **COMO USAR:**

### **Opção 1: Atalho na Área de Trabalho (Recomendado)**

1. **Execute este comando no PowerShell:**

```powershell
cd C:\Users\Usuario\djangoSIGE
.\DEPLOY_AUTOMATICO.bat
```

### **Opção 2: Clique Duplo**

1. Vá em: `C:\Users\Usuario\djangoSIGE`
2. Encontre: `DEPLOY_AUTOMATICO.bat`
3. **Clique duas vezes** nele
4. Siga as instruções na tela

---

## ⚠️ **DURANTE A EXECUÇÃO:**

### **Quando aparecer "Fazendo login no Railway":**
- ✅ Seu navegador vai abrir automaticamente
- ✅ Clique em **"Login with GitHub"**
- ✅ Autorize o Railway
- ✅ Volte para o terminal
- ✅ Pressione qualquer tecla

### **Quando pedir "PostgreSQL":**
- ✅ Use as setas ↑↓ para selecionar **"PostgreSQL"**
- ✅ Pressione **Enter**

### **Quando pedir dados do superusuário:**
- ✅ Digite seu **username** (ex: admin)
- ✅ Digite seu **email** (pode ser qualquer)
- ✅ Digite sua **senha** (mínimo 8 caracteres)
- ✅ Confirme a senha

---

## 🎉 **PRONTO!**

Ao final, o script mostra:

```
✅ SEU SISTEMA ESTÁ ONLINE!

🌐 Acesse: https://seu-projeto.up.railway.app/gerencial/
🔐 Admin: https://seu-projeto.up.railway.app/admin/
```

---

## 💡 **DICA:**

Se quiser ver os logs durante o deploy:

```bash
railway logs --follow
```

---

## 🆘 **SE DER ERRO:**

Execute manualmente:

```bash
cd C:\Users\Usuario\djangoSIGE

# 1. Login
railway login

# 2. Criar projeto
railway init

# 3. Adicionar PostgreSQL
railway add

# 4. Configurar variáveis
railway variables set SECRET_KEY="qm0_t^rrrg!9f5hkk7u@we^u$3(4#i7io@88_1atm6i*49k2=f"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS=".railway.app,.up.railway.app"

# 5. Deploy
railway up

# 6. Migrations
railway run python manage.py migrate

# 7. Criar admin
railway run python manage.py createsuperuser

# 8. Ver URL
railway domain
```

---

## ✅ **ESTÁ TUDO PRONTO! EXECUTE O SCRIPT AGORA!**

```powershell
cd C:\Users\Usuario\djangoSIGE
.\DEPLOY_AUTOMATICO.bat
```

🚀 **Seu sistema vai estar online em ~5 minutos!**
