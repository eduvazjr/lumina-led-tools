# -*- coding: utf-8 -*-

from decimal import Decimal

from django.urls import reverse

from djangosige.apps.cadastro.models import Cliente
from djangosige.apps.contabilidade.models import ApuracaoTributos, Fiscal, ProcessoContabil
from djangosige.tests.test_case import BaseTestCase


class RelatoriosContabilidadeTestCase(BaseTestCase):
    url_processos = reverse('contabilidade:relatorio_processos')
    url_fiscal = reverse('contabilidade:relatorio_fiscal')

    def criar_processo(self, numero, status='fiscal'):
        return ProcessoContabil.objects.create(
            cliente=Cliente.objects.first(), numero_processo=numero, status=status)

    def apurar(self, processo, mes, ano, total, pago=False):
        fiscal, _ = Fiscal.objects.get_or_create(processo=processo)
        return ApuracaoTributos.objects.create(
            fiscal=fiscal, mes_referencia=mes, ano_referencia=ano, receita_bruta=Decimal('1000.00'),
            icms=total, total_tributos=total, pago=pago)

    def test_pagina_inicial_leva_aos_relatorios(self):
        response = self.client.get(reverse('contabilidade:relatorios'))
        self.assertContains(response, self.url_processos)
        self.assertContains(response, self.url_fiscal)

    def test_relatorios_vazios_abrem(self):
        self.assertContains(self.client.get(self.url_processos), 'Nenhum processo encontrado')
        self.assertContains(self.client.get(self.url_fiscal), 'Nenhuma apuração de tributos encontrada')

    def test_relatorio_de_processos(self):
        self.criar_processo('P-1', 'fiscal')
        self.criar_processo('P-2', 'fiscal')
        self.criar_processo('P-3', 'concluido')
        response = self.client.get(self.url_processos)
        etapas = {item['status']: item for item in response.context['status_stats']}
        self.assertEqual(etapas['fiscal']['total'], 2)
        self.assertEqual(etapas['fiscal']['percentual'], 67)
        self.assertEqual(etapas['entrada']['total'], 0)
        self.assertEqual(response.context['total_andamento'], 2)
        self.assertEqual(response.context['total_concluidos'], 1)
        self.assertContains(response, 'P-3')

        filtrado = self.client.get(self.url_processos, {'status': 'concluido'})
        self.assertEqual([p.numero_processo for p in filtrado.context['processos']], ['P-3'])
        self.assertEqual(self.client.get(self.url_processos, {'status': 'xyz'}).context['status_atual'], '')

    def test_relatorio_fiscal_soma_por_mes_e_ano(self):
        um, dois = self.criar_processo('P-1'), self.criar_processo('P-2')
        self.apurar(um, 3, 2026, Decimal('100.00'), pago=True)
        self.apurar(dois, 3, 2026, Decimal('50.00'))
        self.apurar(um, 4, 2026, Decimal('10.00'))
        self.apurar(um, 3, 2025, Decimal('7.00'))

        response = self.client.get(self.url_fiscal)
        self.assertEqual(response.context['ano'], 2026)
        self.assertEqual(response.context['anos'], [2026, 2025])
        self.assertEqual(response.context['resumo']['total'], Decimal('160.00'))
        self.assertEqual(response.context['resumo']['total_pago'], Decimal('100.00'))
        self.assertEqual(response.context['resumo']['pendente'], Decimal('60.00'))
        marco = [m for m in response.context['totais_mensais'] if m['mes_referencia'] == 3][0]
        self.assertEqual(marco['total'], Decimal('150.00'))
        self.assertEqual(marco['pendente'], Decimal('50.00'))
        self.assertContains(response, '03/2026')

        anterior = self.client.get(self.url_fiscal, {'ano': 2025})
        self.assertEqual(anterior.context['resumo']['total'], Decimal('7.00'))
        for invalido in ('abc', '1999'):
            self.assertEqual(self.client.get(self.url_fiscal, {'ano': invalido}).context['ano'], 2026)

    def test_exige_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url_processos).status_code, 302)
        self.assertEqual(self.client.get(self.url_fiscal).status_code, 302)
