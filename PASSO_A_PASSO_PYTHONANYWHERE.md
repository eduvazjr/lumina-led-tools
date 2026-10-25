# ⚡ GUIA RÁPIDO - PYTHONANYWHERE

## ✅ VOCÊ ESTÁ AQUI! PRÓXIMOS PASSOS:

### **1. CONTA CRIADA?** ✅
- Sim → Continue para o passo 2
- Não → Vá em: https://www.pythonanywhere.com/registration/register/beginner/

---

### **2. FAZER LOGIN**

1. Acesse: https://www.pythonanywhere.com/login/
2. Login com username/senha que criou
3. Você verá o **Dashboard**

---

### **3. FAZER UPLOAD DO PROJETO**

**Arquivo para upload:** `C:\Users\Usuario\led-gerencial-pythonanywhere.zip`

1. No PythonAnywhere, clique em **"Files"** (menu superior)
2. Na seção **"Upload a file"**, clique **"Choose File"**
3. Selecione: `C:\Users\Usuario\led-gerencial-pythonanywhere.zip`
4. Clique **"Upload"**
5. Aguarde o upload (pode demorar 1-2 min)

---

### **4. DESCOMPACTAR O PROJETO**

1. Ainda em **"Files"**, clique em **"Open Bash console here"**
2. No console que abrir, digite:

```bash
unzip led-gerencial-pythonanywhere.zip
cd djangoSIGE
ls
```

Você deve ver as pastas do projeto!

---

### **5. CRIAR WEB APP**

1. Clique em **"Web"** (menu superior)
2. Clique **"Add a new web app"**
3. Clique **"Next"** (aceita o domínio grátis `eduvazjr.pythonanywhere.com`)
4. Selecione **"Manual configuration"**
5. Escolha **"Python 3.10"**
6. Clique **"Next"**

---

### **6. CONFIGURAR CAMINHOS**

Na página **"Web"**, na seção **"Code"**:

**Source code:**
```
/home/eduvazjr/djangoSIGE
```

**Working directory:**
```
/home/eduvazjr/djangoSIGE
```

**⚠️ TROQUE `eduvazjr` pelo SEU username se for diferente!**

Clique **"Save"** (ícone de disquete) após cada campo.

---

### **7. CONFIGURAR WSGI**

1. Ainda na página **"Web"**, na seção **"Code"**
2. Clique no link **"WSGI configuration file"** (ex: `/var/www/eduvazjr_pythonanywhere_com_wsgi.py`)
3. **DELETE TODO** o conteúdo do arquivo
4. Cole isto:

```python
import os
import sys

path = '/home/eduvazjr/djangoSIGE'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'djangosige.configs.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**⚠️ TROQUE `eduvazjr` pelo SEU username!**

5. Clique **"Save"** (botão verde no topo)

---

### **8. CONFIGURAR ARQUIVOS ESTÁTICOS**

Ainda na página **"Web"**, na seção **"Static files"**:

Clique **"Enter URL"** e adicione:

**URL:** `/static/`  
**Directory:** `/home/eduvazjr/djangoSIGE/djangosige/static/`

**URL:** `/media/`  
**Directory:** `/home/eduvazjr/djangoSIGE/djangosige/media/`

**⚠️ TROQUE `eduvazjr` pelo SEU username!**

---

### **9. CONFIGURAR VARIÁVEIS DE AMBIENTE**

1. Vá em **"Files"** → Clique em **"Open Bash console here"**
2. Crie arquivo `.env`:

```bash
cd /home/eduvazjr/djangoSIGE
nano .env
```

3. Cole isto:

```
SECRET_KEY=qm0_t^rrrg!9f5hkk7u@we^u$3(4#i7io@88_1atm6i*49k2=f
DEBUG=False
ALLOWED_HOSTS=eduvazjr.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://eduvazjr.pythonanywhere.com
```

**⚠️ TROQUE `eduvazjr` pelo SEU username!**

4. Salve: **Ctrl+O** → **Enter** → **Ctrl+X**

---

### **10. INSTALAR DEPENDÊNCIAS**

No console Bash:

```bash
cd /home/eduvazjr/djangoSIGE
pip3 install --user -r requirements.txt
```

Aguarde ~2-3 minutos.

---

### **11. CONFIGURAR BANCO DE DADOS**

```bash
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser
```

Na última linha, digite:
- **Username:** admin
- **Email:** admin@ledtools.com
- **Password:** (mínimo 8 caracteres)
- Confirme a senha

---

### **12. ATIVAR O SITE**

1. Vá em **"Web"** (menu superior)
2. Clique no botão verde gigante: **"Reload eduvazjr.pythonanywhere.com"**

---

## 🎉 **PRONTO! SEU SISTEMA ESTÁ ONLINE!**

```
🌐 Sistema: https://eduvazjr.pythonanywhere.com/gerencial/
🔐 Admin: https://eduvazjr.pythonanywhere.com/admin/
```

**Login:** admin / sua-senha

---

## 📊 **IMPORTAR OS 369 PAGAMENTOS:**

1. Acesse o admin
2. Vá em **Controle Gerencial** → **Importar Planilha**
3. Faça upload do Excel

---

## 🔄 **PARA ATUALIZAR O CÓDIGO:**

1. Edite arquivos em **"Files"**
2. Vá em **"Web"**
3. Clique **"Reload"**

**SIM! É SÓ ISSO!** 🚀

---

## ⏱️ TEMPO TOTAL: ~10-15 MINUTOS

**100% interface web, zero complexidade!**
