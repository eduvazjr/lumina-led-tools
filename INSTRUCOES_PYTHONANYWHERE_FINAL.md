# 🚀 DEPLOY PYTHONANYWHERE - INSTRUÇÕES FINAIS

## ✅ USERNAME: eduvazjr

---

## 📋 PASSO A PASSO (10 MINUTOS TOTAL):

### **PASSO 1: ABRIR CONSOLE BASH (1 MIN)**

1. Faça login em: https://www.pythonanywhere.com/login/
2. No menu superior, clique em **"Consoles"**
3. Clique em **"Bash"** (na seção "Start a new console")
4. Aguarde o console abrir (tela preta)

---

### **PASSO 2: EXECUTAR SCRIPT 1 (3 MIN)**

No console Bash que abriu, **COPIE E COLE** este comando:

```bash
curl -s https://raw.githubusercontent.com/eduvazjr/lumina-led-tools/main/SCRIPT_1_PYTHONANYWHERE.sh | bash
```

**OU**, se preferir, copie e cole todo o conteúdo do arquivo `SCRIPT_1_PYTHONANYWHERE.sh` diretamente.

**O que vai acontecer:**
- ✅ Clone do projeto do GitHub
- ✅ Instalação de dependências (~2-3 min)
- ✅ Configuração do .env
- ✅ Criação do banco de dados (migrations)
- ✅ Coleta de arquivos estáticos

**Aguarde até aparecer:** `✅ PARTE 1 CONCLUÍDA!`

---

### **PASSO 3: CRIAR SUPERUSUÁRIO (1 MIN)**

Ainda no console Bash, execute:

```bash
cd ~/djangoSIGE
python3 manage.py createsuperuser
```

Digite:
- **Username:** admin
- **Email:** admin@ledtools.com (pode ser qualquer)
- **Password:** (mínimo 8 caracteres - digite duas vezes)

---

### **PASSO 4: CRIAR WEB APP (2 MIN)**

1. No menu superior do PythonAnywhere, clique em **"Web"**
2. Clique no botão **"Add a new web app"**
3. Clique **"Next"** (aceita domínio `eduvazjr.pythonanywhere.com`)
4. Selecione **"Manual configuration"**
5. Escolha **"Python 3.10"**
6. Clique **"Next"**

---

### **PASSO 5: CONFIGURAR CAMINHOS (1 MIN)**

Na página **"Web"** que abriu, na seção **"Code"**:

**Source code:**
```
/home/eduvazjr/djangoSIGE
```
Clique no ícone ✅ (salvar)

**Working directory:**
```
/home/eduvazjr/djangoSIGE
```
Clique no ícone ✅ (salvar)

---

### **PASSO 6: CONFIGURAR WSGI (1 MIN)**

1. Ainda na página **"Web"**, na seção **"Code"**
2. Clique no link do **"WSGI configuration file"**
   - Ex: `/var/www/eduvazjr_pythonanywhere_com_wsgi.py`
3. **DELETE TODO** o conteúdo do arquivo
4. Cole o conteúdo do arquivo **`WSGI_CONFIG.py`** (que está na pasta do projeto)
5. Clique no botão **"Save"** (verde, no topo)

---

### **PASSO 7: CONFIGURAR ARQUIVOS ESTÁTICOS (1 MIN)**

Ainda na página **"Web"**, na seção **"Static files"**:

Clique em **"Enter URL"** e adicione **DUAS** entradas:

**Entrada 1:**
- **URL:** `/static/`
- **Directory:** `/home/eduvazjr/djangoSIGE/djangosige/static/`

**Entrada 2:**
- **URL:** `/media/`
- **Directory:** `/home/eduvazjr/djangoSIGE/djangosige/media/`

Clique no ícone ✅ após cada entrada.

---

### **PASSO 8: ATIVAR O SITE (10 SEGUNDOS)**

1. Role até o topo da página **"Web"**
2. Clique no botão verde gigante: **"Reload eduvazjr.pythonanywhere.com"**
3. Aguarde ~5-10 segundos

---

## 🎉 **PRONTO! SEU SISTEMA ESTÁ ONLINE!**

```
🌐 Sistema: https://eduvazjr.pythonanywhere.com/gerencial/
🔐 Admin: https://eduvazjr.pythonanywhere.com/admin/
```

**Login:** admin / sua-senha

---

## 📊 **IMPORTAR OS 369 PAGAMENTOS:**

1. Acesse: https://eduvazjr.pythonanywhere.com/admin/
2. Login com admin
3. Vá em **"Gerencial"** → **"Pagamentos fornecedor"** → **"Importar"**
4. Ou use a interface: https://eduvazjr.pythonanywhere.com/gerencial/
5. Clique em **"Importar"** e faça upload do Excel

---

## 🔄 **PARA ATUALIZAR O CÓDIGO NO FUTURO:**

1. Faça alterações no seu PC
2. Commit e push para GitHub:
   ```bash
   git add .
   git commit -m "Update"
   git push
   ```
3. No console Bash do PythonAnywhere:
   ```bash
   cd ~/djangoSIGE
   git pull
   ```
4. Vá em **"Web"** → Clique **"Reload"**

---

## 🆘 **PROBLEMAS?**

### **Erro 500:**
- Vá em **"Web"** → clique em **"Error log"**
- Copie o erro e me mostre

### **CSS/JS não carrega:**
```bash
cd ~/djangoSIGE
python3 manage.py collectstatic --noinput
```
Depois: **"Web"** → **"Reload"**

### **Banco de dados vazio:**
```bash
cd ~/djangoSIGE
python3 manage.py migrate
```

---

## ⏱️ **TEMPO TOTAL: ~10 MINUTOS**

**100% gratuito!**
**Interface web simples!**
**Sistema online 24/7!**

---

🎉 **SUCESSO! LED GERENCIAL v7.5 ONLINE NO PYTHONANYWHERE!**
