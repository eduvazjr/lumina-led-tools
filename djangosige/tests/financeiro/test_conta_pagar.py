# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from djangosige.apps.financeiro.models import DocumentoSaida, Saida
from djangosige.tests.test_case import BaseTestCase

MEDIA_TESTE = tempfile.mkdtemp()


def dados_conta(**extra):
    dados = {
        'descricao': 'Conta de teste',
        'numero_documento': 'NF-123',
        'status': '1',
        'data_vencimento': date.today().strftime('%d/%m/%Y'),
        'valor_total': '100,00',
        'abatimento': '0,00',
        'juros': '0,00',
        'valor_liquido': '100,00',
    }
    dados.update(extra)
    return dados


@override_settings(DOCUMENTOS_PRIVADOS_ROOT=MEDIA_TESTE)
class ContaPagarDocumentoStatusTestCase(BaseTestCase):
    url_add = reverse('financeiro:addcontapagarview')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TESTE, ignore_errors=True)

    def adicionar(self, **extra):
        self.client.post(self.url_add, dados_conta(**extra))
        return Saida.objects.get(descricao=extra.get('descricao', 'Conta de teste'))

    def test_formulario_oferece_a_pagar_e_pago(self):
        response = self.client.get(self.url_add)
        status = response.context['form'].fields['status']
        self.assertEqual([c[0] for c in status.choices], ['1', '0'])
        self.assertEqual(dict(status.choices)['0'], 'Pago')
        self.assertNotIn('disabled', status.widget.attrs)
        self.assertContains(response, 'name="numero_documento"')
        self.assertContains(response, 'multipart/form-data')

    def test_conta_a_pagar_salva_numero_sem_data_de_pagamento(self):
        conta = self.adicionar(data_pagamento='01/01/2020')
        self.assertEqual(conta.numero_documento, 'NF-123')
        self.assertEqual(conta.status, '1')
        self.assertIsNone(conta.data_pagamento)

    def test_conta_paga_recebe_data_de_hoje_e_sai_da_lista(self):
        conta = self.adicionar(status='0')
        self.assertEqual(conta.status, '0')
        self.assertEqual(conta.data_pagamento, date.today())
        response = self.client.get(reverse('financeiro:listacontapagarview'))
        self.assertNotIn(conta, response.context['all_contaspagar'])

    def test_conta_paga_pode_voltar_para_a_pagar(self):
        conta = self.adicionar(status='0')
        self.client.post(
            reverse('financeiro:editarpagamentoview', kwargs={'pk': conta.pk}), dados_conta())
        conta.refresh_from_db()
        self.assertEqual(conta.status, '1')
        self.assertIsNone(conta.data_pagamento)

    def test_upload_de_varios_documentos_download_e_remocao(self):
        arquivos = [SimpleUploadedFile('nota.pdf', b'%PDF-1.4 a'),
                    SimpleUploadedFile('boleto.png', b'png')]
        conta = self.adicionar(documentos=arquivos)
        self.assertEqual(conta.documentos.count(), 2)
        self.assertTrue(conta.documentos.first().arquivo.path.startswith(os.path.abspath(MEDIA_TESTE)))

        documento = conta.documentos.get(nome='nota.pdf')
        url = reverse('financeiro:documentosaidaview', kwargs={'pk': documento.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 a')

        caminho = documento.arquivo.path
        self.client.post(reverse('financeiro:editarcontapagarview', kwargs={'pk': conta.pk}),
                         dados_conta(remover_documento=[documento.pk]))
        self.assertFalse(DocumentoSaida.objects.filter(pk=documento.pk).exists())
        self.assertEqual(conta.documentos.count(), 1)
        self.assertFalse(documento.arquivo.storage.exists(caminho))

    def test_upload_recusa_extensao_nao_permitida(self):
        response = self.client.post(self.url_add, dados_conta(
            documentos=[SimpleUploadedFile('script.html', b'<script>')]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['documentos'])
        self.assertFalse(Saida.objects.filter(descricao='Conta de teste').exists())

    def test_download_exige_login(self):
        conta = self.adicionar(documentos=[SimpleUploadedFile('nota.pdf', b'x')])
        url = reverse('financeiro:documentosaidaview',
                      kwargs={'pk': conta.documentos.get().pk})
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_alertas_de_vencimento_na_lista(self):
        hoje = date.today()
        Saida.objects.all().delete()
        comum = {'status': '1', 'valor_liquido': Decimal('10.00')}
        Saida.objects.create(descricao='vencida', data_vencimento=hoje - timedelta(days=2), **comum)
        Saida.objects.create(descricao='hoje', data_vencimento=hoje, **comum)
        Saida.objects.create(descricao='proxima', data_vencimento=hoje + timedelta(days=3), **comum)
        Saida.objects.create(descricao='longe', data_vencimento=hoje + timedelta(days=30), **comum)

        response = self.client.get(reverse('financeiro:listacontapagarview'))
        self.assertContains(response, '1 conta a pagar vencida')
        self.assertContains(response, '1 conta a pagar vence hoje')
        self.assertContains(response, '1 conta a pagar vence nos próximos 7 dias')
        self.assertContains(response, 'Vencida há 2 dias')
        self.assertContains(response, 'Vence em 3 dias')

    def test_plano_de_contas_volta_para_a_tela_anterior(self):
        url_plano = reverse('financeiro:planocontasview')
        lista = reverse('financeiro:listacontapagarview')
        self.assertEqual(str(self.client.get(url_plano).context['voltar_url']), lista)

        self.client.get(self.url_add)
        response = self.client.get(url_plano)
        self.assertEqual(response.context['voltar_url'], self.url_add)
        self.assertContains(response, 'Voltar')

        self.adicionar()
        self.assertEqual(str(self.client.get(url_plano).context['voltar_url']), lista)
