# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from django.urls import reverse

from djangosige.tests.test_case import BaseTestCase
from djangosige.apps.cadastro.models import Cliente
from djangosige.apps.contabilidade.models import (
    ProcessoContabil, DepartamentoPessoal, Funcionario, FolhaPagamento)


class MenuRHTestCase(BaseTestCase):

    def setUp(self):
        super(MenuRHTestCase, self).setUp()
        processo = ProcessoContabil.objects.create(
            cliente=Cliente.objects.first(), numero_processo='RH-001')
        self.dp = DepartamentoPessoal.objects.create(processo=processo)
        Funcionario.objects.create(
            dp=self.dp, nome_completo='Ana Souza', cpf='111.111.111-11',
            data_nascimento=date(1990, 1, 1), data_admissao=date(2024, 3, 1),
            cargo='Vendedora', salario=Decimal('2500.00'))
        Funcionario.objects.create(
            dp=self.dp, nome_completo='Bruno Lima', cpf='222.222.222-22',
            data_nascimento=date(1985, 5, 5), data_admissao=date(2020, 1, 10),
            cargo='Estoquista', salario=Decimal('2000.00'), ativo=False)
        FolhaPagamento.objects.create(
            dp=self.dp, mes_referencia=9, ano_referencia=2026,
            total_liquido=Decimal('2500.00'))

    def test_menu_mostra_rh_e_importacao(self):
        response = self.client.get(reverse('base:index'))
        self.assertContains(response, reverse('contabilidade:rh_funcionarios'))
        self.assertContains(response, reverse('contabilidade:rh_folhas'))
        self.assertContains(response, reverse('contabilidade:rh_departamentos'))
        self.assertContains(response, reverse('base:importacaoview', args=['planilha']))
        self.assertContains(response, reverse('base:importacaoview', args=['nfe-entrada']))
        self.assertContains(response, reverse('base:importacaoview', args=['nfe-saida']))

    def test_funcionarios_filtra_situacao_e_busca(self):
        url = reverse('contabilidade:rh_funcionarios')
        response = self.client.get(url)
        self.assertContains(response, 'Ana Souza')
        self.assertContains(response, 'Bruno Lima')
        self.assertEqual(response.context['total_ativos'], 1)
        self.assertEqual(response.context['folha_salarial'], Decimal('2500.00'))

        response = self.client.get(url, {'situacao': 'ativos'})
        self.assertNotContains(response, 'Bruno Lima')

        response = self.client.get(url, {'q': 'estoquista'})
        self.assertContains(response, 'Bruno Lima')
        self.assertNotContains(response, 'Ana Souza')

    def test_folhas_e_departamentos(self):
        response = self.client.get(reverse('contabilidade:rh_folhas'))
        self.assertContains(response, '09/2026')
        self.assertEqual(response.context['total_pendentes'], 1)

        response = self.client.get(reverse('contabilidade:rh_departamentos'))
        self.assertContains(response, 'RH-001')
        self.assertEqual(response.context['departamentos'][0].qtd_funcionarios, 1)

    def test_telas_por_departamento(self):
        response = self.client.get(reverse('contabilidade:rh_dp_funcionarios', args=[self.dp.pk]))
        self.assertContains(response, 'Ana Souza')
        response = self.client.get(reverse('contabilidade:rh_dp_folhas', args=[self.dp.pk]))
        self.assertContains(response, '09/2026')


class MenuImportacaoTestCase(BaseTestCase):

    def test_telas_de_importacao(self):
        casos = {
            'planilha': ('gerencial:importar_planilha', 'name="arquivo"'),
            'nfe-entrada': ('fiscal:importarnotafiscalentrada', 'name="arquivo_xml"'),
            'nfe-saida': ('fiscal:importarnotafiscalsaida', 'name="arquivo_xml"'),
        }
        for tipo, (destino, campo) in casos.items():
            response = self.client.get(reverse('base:importacaoview', args=[tipo]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'action="%s"' % reverse(destino))
            self.assertContains(response, campo)

        response = self.client.get(reverse('base:importacaoview', args=['nfe-entrada']))
        self.assertContains(response, 'name="fornecedor"')

    def test_tipo_inexistente(self):
        response = self.client.get(reverse('base:importacaoview', args=['outro']))
        self.assertEqual(response.status_code, 404)
