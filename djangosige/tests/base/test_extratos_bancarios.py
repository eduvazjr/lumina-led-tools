# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from djangosige.apps.cadastro.models import Empresa, PessoaJuridica
from djangosige.apps.financeiro_grupo.models import ExtratoBancario
from djangosige.apps.financeiro_grupo.views import _ultimos_meses

PASTA = tempfile.mkdtemp()


@override_settings(DOCUMENTOS_PRIVADOS_ROOT=PASTA)
class ExtratosBancariosTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_superuser('extratos', 'e@t.com', 'senha-de-teste')
        self.client.force_login(self.user)
        self.empresa = Empresa.objects.create(nome_razao_social='Led Tools Importadora Ltda', tipo_pessoa='PJ')
        PessoaJuridica.objects.create(pessoa_id=self.empresa, nome_fantasia='Led Importadora')
        self.ano, self.mes = _ultimos_meses(date.today(), 1)[0]

    def enviar(self, nome='extrato.pdf', conteudo=b'%PDF-1.4 extrato', **extra):
        dados = {'empresa': self.empresa.pk, 'banco': 'Itaú', 'conta': '1234 / 5678-9',
                 'mes': self.mes, 'ano': self.ano, 'saldo_final': '12.345,67',
                 'arquivo': SimpleUploadedFile(nome, conteudo)}
        dados.update(extra)
        return self.client.post(reverse('financeiro_grupo:extrato_add'), dados)

    def test_tela_vazia_mostra_meses_faltando(self):
        response = self.client.get(reverse('financeiro_grupo:extratos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Led Importadora')
        self.assertEqual(response.context['faltando'], 12)
        self.assertContains(response, 'Nenhum extrato encontrado')

    def test_envia_baixa_e_remove_extrato(self):
        response = self.enviar()
        self.assertRedirects(response, reverse('financeiro_grupo:extratos'))
        extrato = ExtratoBancario.objects.get()
        self.assertEqual(extrato.saldo_final, Decimal('12345.67'))
        self.assertEqual(extrato.nome_arquivo, 'extrato.pdf')
        self.assertEqual(extrato.enviado_por, self.user)
        self.assertTrue(extrato.arquivo.path.startswith(os.path.abspath(PASTA)))

        response = self.client.get(reverse('financeiro_grupo:extratos'))
        self.assertEqual(response.context['faltando'], 11)
        self.assertContains(response, 'R$ 12.345,67')

        response = self.client.get(reverse('financeiro_grupo:extrato_baixar', args=[extrato.pk]))
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 extrato')
        response.close()

        caminho = extrato.arquivo.path
        self.client.post(reverse('financeiro_grupo:extrato_remover', args=[extrato.pk]))
        self.assertFalse(ExtratoBancario.objects.exists())
        self.assertFalse(os.path.exists(caminho))

    def test_aceita_ofx_e_recusa_executavel(self):
        self.enviar(nome='extrato.ofx', conteudo=b'OFXHEADER:100')
        self.assertEqual(ExtratoBancario.objects.count(), 1)
        response = self.enviar(nome='programa.exe', conteudo=b'MZ')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'não é aceito')
        self.assertEqual(ExtratoBancario.objects.count(), 1)

    def test_editar_sem_novo_arquivo_mantem_o_atual(self):
        self.enviar()
        extrato = ExtratoBancario.objects.get()
        response = self.client.post(reverse('financeiro_grupo:extrato_edit', args=[extrato.pk]), {
            'empresa': self.empresa.pk, 'banco': 'Bradesco', 'conta': '', 'mes': self.mes, 'ano': self.ano,
            'saldo_final': '', 'observacoes': ''})
        self.assertRedirects(response, reverse('financeiro_grupo:extratos'))
        extrato.refresh_from_db()
        self.assertEqual(extrato.banco, 'Bradesco')
        self.assertEqual(extrato.nome_arquivo, 'extrato.pdf')
        self.assertIsNone(extrato.saldo_final)

    def test_exige_login(self):
        self.enviar()
        extrato = ExtratoBancario.objects.get()
        self.client.logout()
        response = self.client.get(reverse('financeiro_grupo:extrato_baixar', args=[extrato.pk]))
        self.assertEqual(response.status_code, 302)
