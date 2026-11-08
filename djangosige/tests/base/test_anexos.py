import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, RequestContext, Template
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from djangosige.apps.anexos.models import Anexo
from djangosige.apps.cadastro.models import Cliente

PASTA = tempfile.mkdtemp()


@override_settings(DOCUMENTOS_PRIVADOS_ROOT=PASTA)
class AnexosTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA, ignore_errors=True)

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser('anexo_admin', 'a@a.com', 'senha-teste')
        self.leitor = User.objects.create_user('anexo_leitor', password='senha-teste')
        self.leitor.user_permissions.add(Permission.objects.get(codename='view_cliente'))
        self.sem_acesso = User.objects.create_user('anexo_sem', password='senha-teste')
        self.cliente = Cliente.objects.create(nome_razao_social='Cliente Anexo', tipo_pessoa='PJ')
        self.ct = ContentType.objects.get_for_model(Cliente)
        self.url_enviar = reverse('anexos:enviar', args=[self.ct.pk, self.cliente.pk])

    def _pdf(self, nome='contrato.pdf'):
        return SimpleUploadedFile(nome, b'%PDF-1.4 teste', content_type='application/pdf')

    def test_quem_edita_envia_e_remove(self):
        self.client.force_login(self.admin)
        r = self.client.post(self.url_enviar, {'arquivos': [self._pdf(), self._pdf('foto.png')], 'next': '/cadastro/'})
        self.assertRedirects(r, '/cadastro/#documentos', fetch_redirect_response=False)
        self.assertEqual(Anexo.objects.filter(object_id=self.cliente.pk, content_type=self.ct).count(), 2)
        anexo = Anexo.objects.get(nome='contrato.pdf')
        self.assertEqual(anexo.enviado_por, self.admin)
        r = self.client.get(reverse('anexos:baixar', args=[anexo.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(b''.join(r.streaming_content), b'%PDF-1.4 teste')
        self.client.post(reverse('anexos:remover', args=[anexo.pk]), {'next': '/cadastro/'})
        self.assertFalse(Anexo.objects.filter(pk=anexo.pk).exists())

    def test_extensao_nao_permitida_e_recusada_com_aviso(self):
        self.client.force_login(self.admin)
        self.client.post(self.url_enviar, {'arquivos': [SimpleUploadedFile('virus.exe', b'MZ')]})
        self.assertFalse(Anexo.objects.exists())
        self.assertEqual(self.client.session['anexos_aviso']['tipo'], 'erro')
        self.assertIn('exe', self.client.session['anexos_aviso']['texto'])

    def test_quem_so_ve_baixa_mas_nao_envia_nem_remove(self):
        self.client.force_login(self.admin)
        self.client.post(self.url_enviar, {'arquivos': [self._pdf()]})
        anexo = Anexo.objects.get()
        self.client.force_login(self.leitor)
        self.assertEqual(self.client.post(self.url_enviar, {'arquivos': [self._pdf()]}).status_code, 403)
        self.assertEqual(self.client.get(reverse('anexos:baixar', args=[anexo.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse('anexos:remover', args=[anexo.pk])).status_code, 403)
        self.client.force_login(self.sem_acesso)
        self.assertEqual(self.client.get(reverse('anexos:baixar', args=[anexo.pk])).status_code, 403)

    def test_redirecionamento_externo_e_ignorado(self):
        self.client.force_login(self.admin)
        r = self.client.post(self.url_enviar, {'arquivos': [self._pdf()], 'next': 'https://site-malicioso.com/'})
        self.assertEqual(r['Location'], '/#documentos')

    def test_bloco_aparece_conforme_permissao(self):
        modelo = Template('{% load anexos %}{% documentos objeto %}')
        for usuario, ve, envia in [(self.admin, True, True), (self.leitor, True, False), (self.sem_acesso, False, False)]:
            request = RequestFactory().get('/cadastro/cliente/editar/%d/' % self.cliente.pk)
            request.user = usuario
            html = modelo.render(RequestContext(request, {'objeto': self.cliente}))
            self.assertEqual('id="documentos"' in html, ve, usuario.username)
            self.assertEqual('name="arquivos"' in html, envia, usuario.username)
