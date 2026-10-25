# 🚀 DEPLOY SUPER FÁCIL - PYTHONANYWHERE

## ✅ A MANEIRA MAIS FÁCIL DE COLOCAR DJANGO ONLINE

**SEM:** Terminal, Railway, Render, PostgreSQL, comandos complexos
**COM:** Interface web simples, cliques, drag-and-drop

---

## 📋 PASSO A PASSO (5 MINUTOS):

### **1. CRIAR CONTA (1 MIN)**

1. Acesse: https://www.pythonanywhere.com
2. Clique em **"Pricing & signup"**
3. Escolha **"Create a Beginner account"** (GRÁTIS)
4. Preencha: username, email, senha
5. Confirme o email

---

### **2. FAZER UPLOAD DO PROJETO (2 MIN)**

**Opção A - Upload ZIP (Mais Fácil):**

1. No seu PC, vá em: `C:\Users\Usuario\djangoSIGE`
2. Selecione TODAS as pastas (exceto `.git`)
3. Clique direito → Enviar para → Pasta compactada
4. Salve como: `led-gerencial.zip`
5. No PythonAnywhere:
   - Vá em **"Files"** (menu superior)
   - Clique **"Upload a file"**
   - Escolha `led-gerencial.zip`
   - Aguarde upload
6. No console Bash:
   ```bash
   unzip led-gerencial.zip
   ```

**Opção B - Git Clone:**

1. No PythonAnywhere, vá em **"Consoles"** → **"Bash"**
2. Execute:
   ```bash
   git clone https://github.com/eduvazjr/lumina-led-tools.git
   cd lumina-led-tools
   ```

---

### **3. CONFIGURAR WEB APP (1 MIN)**

1. Vá em **"Web"** (menu superior)
2. Clique **"Add a new web app"**
3. Clique **"Next"** (aceita o domínio gratuito)
4. Selecione **"Manual configuration"**
5. Escolha **"Python 3.10"**
6. Clique **"Next"**

---

### **4. CONFIGURAR SETTINGS (1 MIN)**

Na página do Web App:

**Source code:**
```
/home/SEU_USERNAME/lumina-led-tools
```

**Working directory:**
```
/home/SEU_USERNAME/lumina-led-tools
```

**WSGI configuration file:**
- Clique no link (ex: `/var/www/seu_username_pythonanywhere_com_wsgi.py`)
- **DELETE TODO** o conteúdo
- Cole isto:

```python
import os
import sys

path = '/home/SEU_USERNAME/lumina-led-tools'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'djangosige.configs.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**⚠️ TROQUE `SEU_USERNAME` pelo seu username PythonAnywhere!**

- Clique **"Save"**

---

### **5. INSTALAR DEPENDÊNCIAS E ATIVAR**

1. Vá em **"Consoles"** → **"Bash"**
2. Execute:

```bash
cd lumina-led-tools

# Instalar dependências
pip3 install --user -r requirements.txt

# Criar banco de dados
python3 manage.py migrate

# Coletar arquivos estáticos
python3 manage.py collectstatic --noinput

# Criar superusuário
python3 manage.py createsuperuser
```

3. Digite username/email/senha do admin

4. Vá em **"Web"** novamente
5. Clique no botão verde **"Reload seu_username.pythonanywhere.com"**

---

## 🎉 PRONTO!

Seu sistema está online em:

```
https://seu_username.pythonanywhere.com/gerencial/
https://seu_username.pythonanywhere.com/admin/
```

---

## ✅ VANTAGENS PYTHONANYWHERE:

- ✅ Interface web para tudo
- ✅ Restart com 1 clique
- ✅ Editor de código online
- ✅ Logs visíveis na interface
- ✅ MySQL gratuito
- ✅ HTTPS incluído
- ✅ Backup fácil
- ✅ Sem sleep (sempre online)

---

## 🆓 LIMITAÇÕES PLANO GRÁTIS:

- ⚠️ Apenas 1 aplicação web
- ⚠️ 512 MB de espaço
- ⚠️ Domínio: `usuario.pythonanywhere.com` (não customizável)
- ⚠️ CPU limitada (suficiente para uso pessoal/demonstração)

**Upgrade:** $5/mês remove todas as limitações

---

## 💡 DICA:

Para **importar os 369 pagamentos**:

1. Acesse: `https://seu_username.pythonanywhere.com/admin`
2. Login com o superusuário
3. Vá em **Controle Gerencial** → **Importar Planilha**
4. Upload do Excel

---

## 🆘 PROBLEMAS?

### **Erro 500:**
- Vá em **"Web"** → **"Error log"**
- Veja o erro
- Geralmente é `ALLOWED_HOSTS` ou `SECRET_KEY`

### **Arquivos estáticos não carregam:**
```bash
python3 manage.py collectstatic --noinput
```

### **Mudar algo no código:**
- Edite na interface **"Files"**
- Clique **"Reload"** no Web

---

## ⏱️ TEMPO TOTAL: ~5-10 MINUTOS

**ZERO linha de comando complexa!**
**ZERO configuração de servidor!**
**100% interface web!**

---

🎉 **A MANEIRA MAIS FÁCIL DE TER SEU DJANGO ONLINE!**
