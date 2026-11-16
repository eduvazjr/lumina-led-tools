# -*- coding: utf-8 -*-

from types import SimpleNamespace

from djangosige.tests.test_case import BaseTestCase, TEST_USERNAME, TEST_PASSWORD
from djangosige.apps.cadastro.models import Empresa, MinhaEmpresa
from djangosige.apps.login.models import Usuario
from djangosige.apps.login.adapters import ExistingUserSocialAccountAdapter

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.db.models import Q


class UserFormViewTestCase(BaseTestCase):

    def test_user_logged_in_redirect(self):
        url = reverse('login:loginview')

        # Assert login redirect se usuario logado
        response = self.client.get(url)
        self.assertEqual(response.url, '/')

        # Assert abre pagina se usuario nao logado
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')

    def test_user_login(self):
        url = reverse('login:loginview')
        self.client.logout()
        data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base/index.html')

    @override_settings(GOOGLE_LOGIN_ENABLED=False)
    def test_google_login_hidden_without_credentials(self):
        self.client.logout()
        response = self.client.get(reverse('login:loginview'))
        self.assertNotContains(response, 'Continuar com Google')

    @override_settings(
        GOOGLE_LOGIN_ENABLED=True,
        SOCIALACCOUNT_PROVIDERS={
            'google': {
                'APP': {
                    'client_id': 'test-client-id',
                    'secret': 'test-client-secret',
                    'key': '',
                },
            },
        },
    )
    def test_google_login_button_uses_post(self):
        self.client.logout()
        response = self.client.get(reverse('login:loginview'))
        self.assertContains(response, 'Continuar com Google')
        self.assertContains(
            response,
            'action="/accounts/google/login/?process=login"',
        )
        self.assertContains(response, 'method="post"')

    def test_social_signup_is_closed(self):
        adapter = ExistingUserSocialAccountAdapter()
        self.assertFalse(adapter.is_open_for_signup(None, None))

    def test_google_email_requires_one_active_user(self):
        email = 'usuario-google@example.com'
        self.user.email = email
        self.user.save(update_fields=['email'])

        adapter = ExistingUserSocialAccountAdapter()
        adapter.can_authenticate_by_email = lambda sociallogin, value: True
        sociallogin = SimpleNamespace(
            email_addresses=[SimpleNamespace(email=email, verified=True)],
        )

        matched_user, matched_email = adapter.authenticate_by_email(sociallogin)
        self.assertEqual(matched_user, self.user)
        self.assertEqual(matched_email, email)

        User.objects.create_user(
            username='usuario-google-duplicado',
            email=email,
        )
        self.assertIsNone(adapter.authenticate_by_email(sociallogin))


class UserRegistrationFormViewTestCase(BaseTestCase):

    def test_registration_view_get_request(self):
        url = reverse('login:registrarview')
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/registrar.html')

    def test_user_registration(self):
        url = reverse('login:registrarview')
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        data = {
            'username': 'newUser',
            'password': 'password1234',
            'confirm': 'password1234',
            'email': 'newUser@email.com',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newUser').exists())

        # E-mail precisa identificar um unico usuario para o login Google.
        data = {
            'username': 'newUserDuplicateEmail',
            'password': 'password1234',
            'confirm': 'password1234',
            'email': 'newUser@email.com',
        }
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response.context['form'],
            'email',
            'Este e-mail já está vinculado a outro usuário.',
        )
        self.assertFalse(
            User.objects.filter(username='newUserDuplicateEmail').exists())

        # Assert form invalido (senhas diferentes)
        data = {
            'username': 'newUser2',
            'password': 'password1234',
            'confirm': 'diferente',
            'email': 'newUser2@email.com',
        }
        response = self.client.post(url, data, follow=True)
        self.assertFormError(
            response.context['form'], 'password', 'Senhas diferentes.')

    def test_superuser_required(self):
        url = reverse('login:registrarview')
        # Assert usuario redirect para index se nao e administrador
        self.user.is_superuser = False
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.url, '/')


class UserLogoutViewTestCase(BaseTestCase):

    def test_user_logout_redirect(self):
        url = reverse('login:logoutview')
        response = self.client.get(url)
        self.assertEqual(response.url, '/login/')


class ForgotPasswordViewTestCase(BaseTestCase):

    def test_forgot_view_get_request(self):
        url = reverse('login:esqueceuview')

        # Assert login redirect se usuario logado
        response = self.client.get(url)
        self.assertEqual(response.url, '/')

        # Assert abre pagina se usuario nao logado
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/esqueceu_senha.html')


class MeuPerfilViewTestCase(BaseTestCase):

    def test_perfil_get_request(self):
        url = reverse('login:perfilview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class EditarPerfilViewTestCase(BaseTestCase):

    def test_editar_perfil_view(self):
        url = reverse('login:editarperfilview')
        m_empresa = Empresa.objects.create()
        usuario = Usuario.objects.get(user=self.user)

        # Sem MinhaEmpresa cadastrada
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Adicionar MinhaEmpresa pela view
        data = response.context['form'].initial
        data['username'] = response.context['user'].username
        data['first_name'] = response.context['user'].first_name
        data['last_name'] = response.context['user'].last_name
        data['email'] = response.context['user'].email
        data['m_empresa_form-m_empresa'] = m_empresa.pk

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/perfil.html')
        self.assertEqual(usuario.empresa_usuario.all()[
                         0].m_empresa.pk, m_empresa.pk)


class SelecionarMinhaEmpresaViewTestCase(BaseTestCase):

    def test_selecionar_empresa_view(self):
        url = reverse('login:selecionarempresaview')
        m_empresa = Empresa.objects.create()
        usuario = Usuario.objects.get(user=self.user)
        MinhaEmpresa.objects.filter(m_usuario=usuario).delete()

        # Usuario sem MinhaEmpresa
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'login/selecionar_minha_empresa.html')

        data = {'m_empresa': m_empresa.pk, }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario.empresa_usuario.all()[
                         0].m_empresa.pk, m_empresa.pk)

        # Usuario com MinhaEmpresa
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'login/selecionar_minha_empresa.html')

        m_empresa = Empresa.objects.filter(~Q(id=m_empresa.pk)).first()
        data = {'m_empresa': m_empresa.pk, }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario.empresa_usuario.all()[
                         0].m_empresa.pk, m_empresa.pk)


class UsuariosListViewTestCase(BaseTestCase):

    def test_deletar_usuario(self):
        url = reverse('login:usuariosview')
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        # Testar GET request lista
        obj = User.objects.create(
            username='usuario-google',
            email='usuario@example.com',
        )
        SocialAccount.objects.create(
            user=obj,
            provider='google',
            uid='google-test-uid',
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(obj in response.context['object_list'])
        self.assertTemplateUsed(response, 'login/lista_users.html')
        self.assertContains(response, 'usuario@example.com')
        self.assertContains(response, 'Vinculado')

        # Deletar objeto criado por POST request
        data = {
            obj.pk: 'on',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(obj in response.context['object_list'])


class UsuarioDetailViewTestCase(BaseTestCase):

    def test_usuario_detail_get_request(self):
        url = reverse('login:usuariodetailview', kwargs={'pk': self.user.pk})
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/detalhe_users.html')


class DeletarUsuarioViewTestCase(BaseTestCase):

    def test_deletar_usuario_view(self):
        new_user = User.objects.create()
        url = reverse('login:deletarusuarioview', kwargs={'pk': new_user.pk})
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(new_user in response.context['object_list'])
