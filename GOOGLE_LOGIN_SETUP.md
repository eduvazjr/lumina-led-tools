# Ativacao do login com Google

O sistema aceita o Google somente como forma adicional de autenticar usuarios
ativos que ja foram cadastrados em **Usuarios e acessos**. O e-mail confirmado
pelo Google precisa ser igual ao e-mail de um unico usuario no sistema. Contas
novas nao sao criadas pelo login social e e-mails duplicados nao sao vinculados.

## 1. Configurar o Google Cloud

No Google Cloud Console, crie ou selecione um projeto, configure a tela de
consentimento OAuth e crie uma credencial do tipo **Aplicativo da Web**.

Cadastre exatamente:

- Origem JavaScript autorizada: `https://eduvazjr.pythonanywhere.com`
- URI de redirecionamento autorizada:
  `https://eduvazjr.pythonanywhere.com/accounts/google/login/callback/`

Se o aplicativo OAuth estiver no modo de teste, adicione os usuarios que
poderao entrar como usuarios de teste.

## 2. Configurar o servidor

Adicione ao arquivo `.env` usado pela aplicacao, sem aspas:

```env
GOOGLE_OAUTH_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=seu-client-secret
```

Depois de atualizar o codigo, instale as dependencias e aplique as migracoes:

```bash
cd ~/djangoSIGE
pip install -r requirements.txt
python manage.py migrate
```

Por fim, recarregue o Web App no painel do PythonAnywhere.

## 3. Liberar cada usuario

Em **Usuarios e acessos**, informe no cadastro do usuario o mesmo e-mail usado
na conta Google. No primeiro login, o vinculo sera feito automaticamente apenas
depois que o Google confirmar esse e-mail.

As credenciais do Google nunca devem ser adicionadas ao GitHub. Os tokens de
acesso do Google tambem nao sao armazenados pelo sistema.
