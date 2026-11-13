# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from djangosige.apps.gerencial import calendario
from djangosige.apps.gerencial.models import PagamentoNegociacao
from djangosige.apps.gerencial.templatetags.gerencial_format import fornecedores_por_negociado

PASTA = tempfile.mkdtemp()
HOJE = timezone.localdate()


def planilha(*records):
    return {'records': list(records), 'synced_at': '2026-11-13T12:00:00-03:00', 'is_stale': False, 'sync_error': ''}


class CalendarioTests(TestCase):
    def test_situacao_de_cada_vencimento(self):
        hoje = date(2026, 11, 13)
        base = {'installment_value': Decimal('100'), 'total_value': Decimal('1000'), 'installment_count': Decimal('10')}
        self.assertEqual(calendario.vencimento(dict(base, paid_installments=10, due_date=date(2026, 11, 1)), hoje)['status'], 'pago')
        self.assertEqual(calendario.vencimento(dict(base, paid_installments=3, due_date=date(2026, 11, 1)), hoje)['status'], 'vencido')
        futuro = calendario.vencimento(dict(base, paid_installments=3, due_date=date(2026, 11, 20)), hoje)
        self.assertEqual((futuro['status'], futuro['valor'], futuro['parcelas']), ('futuro', Decimal('100'), '3 de 10 pagas'))
        pago = calendario.vencimento({'payment_value': Decimal('50'), 'due_date': date(2026, 11, 1)}, hoje)
        self.assertEqual((pago['status'], pago['valor']), ('pago', Decimal('50')))

    def test_participacao_no_total_negociado(self):
        linhas = fornecedores_por_negociado({
            'A': {'total_negotiated': Decimal('75'), 'received_estimate': Decimal('75')},
            'B': {'total_negotiated': Decimal('25'), 'received_estimate': Decimal('0')},
        })
        self.assertEqual([(l['nome'], l['participacao'], l['pct']) for l in linhas],
                         [('A', Decimal('75'), Decimal('100')), ('B', Decimal('25'), Decimal('0'))])

    def test_resumo_do_mes(self):
        hoje = date(2026, 11, 13)
        records = [
            {'supplier': 'A', 'due_date': date(2026, 11, 5), 'installment_value': Decimal('100'), 'installment_count': 2, 'paid_installments': 0},
            {'supplier': 'B', 'due_date': date(2026, 11, 20), 'installment_value': Decimal('40'), 'installment_count': 1, 'paid_installments': 0},
            {'supplier': 'C', 'due_date': date(2026, 12, 2), 'installment_value': Decimal('999'), 'installment_count': 1, 'paid_installments': 0},
        ]
        cal = calendario.montar(records, [], 2026, 11, hoje)
        self.assertEqual((cal['resumo']['vencido'], cal['resumo']['a_vencer']), (Decimal('100'), Decimal('40')))
        self.assertEqual(cal['nome_mes'], 'Novembro')
        dias = {d['data']: d for semana in cal['semanas'] for d in semana}
        self.assertEqual(dias[date(2026, 12, 2)]['itens'][0]['fornecedor'], 'C')  # aparece, mas fora do resumo


@override_settings(DOCUMENTOS_PRIVADOS_ROOT=PASTA)
class PagamentoComComprovanteTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_superuser('ger', 'g@t.com', 'senha-de-teste')
        self.client.force_login(self.user)

    @patch('djangosige.apps.gerencial.views.load_negotiations')
    def test_calendario_aparece_no_controle_gerencial(self, load):
        load.return_value = planilha(
            {'supplier': 'Nakasaki', 'order_number': '77', 'product': 'Lote', 'total_value': Decimal('1000'),
             'installment_value': Decimal('250'), 'installment_count': Decimal('4'), 'paid_installments': Decimal('1'),
             'due_date': HOJE + timedelta(days=1) if (HOJE + timedelta(days=1)).month == HOJE.month else HOJE},
            {'supplier': 'Lucas', 'order_number': '8', 'product': 'Lote', 'total_value': Decimal('3000'),
             'installment_value': Decimal('3000'), 'installment_count': Decimal('1'), 'paid_installments': Decimal('0'),
             'due_date': HOJE})
        PagamentoNegociacao.objects.create(fornecedor='Lucas', data=HOJE, valor=Decimal('500'))
        response = self.client.get(reverse('gerencial:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calendário de pagamentos')
        self.assertContains(response, 'Nakasaki · 77')
        self.assertContains(response, '1 de 4 pagas')
        self.assertContains(response, 'Pago · Lucas')
        self.assertContains(response, '75,0%')   # Lucas: 3000 de 4000
        self.assertContains(response, 'width: 75.0%')
        self.assertContains(response, '25,0%')

    @patch('djangosige.apps.gerencial.views.load_negotiations')
    def test_registra_pagamento_com_comprovante(self, load):
        load.return_value = planilha()
        url = reverse('gerencial:pagamento_negociacao_add') + '?fornecedor=Nakasaki&pedido=77&valor=250,00&data=2026-11-10'
        response = self.client.get(url)
        self.assertContains(response, 'value="Nakasaki"')
        self.assertContains(response, 'value="250,00"')
        response = self.client.post(url, {
            'fornecedor': 'Nakasaki', 'pedido': '77', 'data': '2026-11-10', 'valor': '1.250,50',
            'observacao': 'PIX', 'comprovante': SimpleUploadedFile('pix.pdf', b'%PDF-1.4 comprovante')})
        pagamento = PagamentoNegociacao.objects.get()
        self.assertRedirects(response, reverse('gerencial:dashboard') + '?cal_ano=2026&cal_mes=11#calendario',
                             fetch_redirect_response=False)
        self.assertEqual((pagamento.valor, pagamento.nome_comprovante, pagamento.usuario), (Decimal('1250.50'), 'pix.pdf', self.user))
        self.assertTrue(pagamento.comprovante.path.startswith(os.path.abspath(PASTA)))

        arquivo = self.client.get(reverse('gerencial:pagamento_negociacao_comprovante', args=[pagamento.pk]))
        self.assertEqual(b''.join(arquivo.streaming_content), b'%PDF-1.4 comprovante')
        arquivo.close()

        # Trocar o comprovante apaga o arquivo antigo
        antigo = pagamento.comprovante.path
        self.client.post(reverse('gerencial:pagamento_negociacao_edit', args=[pagamento.pk]), {
            'fornecedor': 'Nakasaki', 'pedido': '77', 'data': '2026-11-10', 'valor': '1.250,50',
            'comprovante': SimpleUploadedFile('pix2.jpg', b'jpg')})
        pagamento.refresh_from_db()
        self.assertEqual(pagamento.nome_comprovante, 'pix2.jpg')
        self.assertFalse(os.path.exists(antigo))

        novo = pagamento.comprovante.path
        self.client.post(reverse('gerencial:pagamento_negociacao_remover', args=[pagamento.pk]))
        self.assertFalse(PagamentoNegociacao.objects.exists())
        self.assertFalse(os.path.exists(novo))

    @patch('djangosige.apps.gerencial.views.load_negotiations')
    def test_recusa_arquivo_que_nao_e_comprovante(self, load):
        load.return_value = planilha()
        response = self.client.post(reverse('gerencial:pagamento_negociacao_add'), {
            'fornecedor': 'Nakasaki', 'data': '2026-11-10', 'valor': '10,00',
            'comprovante': SimpleUploadedFile('virus.exe', b'MZ')})
        self.assertContains(response, 'não é aceito')
        self.assertFalse(PagamentoNegociacao.objects.exists())

    def test_comprovante_exige_login(self):
        pagamento = PagamentoNegociacao.objects.create(fornecedor='A', data=HOJE, valor=1)
        self.client.logout()
        response = self.client.get(reverse('gerencial:pagamento_negociacao_comprovante', args=[pagamento.pk]))
        self.assertEqual(response.status_code, 302)
