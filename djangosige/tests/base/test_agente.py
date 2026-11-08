# -*- coding: utf-8 -*-

from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from djangosige.tests.test_case import BaseTestCase
from djangosige.apps.base import agente
from djangosige.apps.cadastro.models import Cliente, Fornecedor, Empresa, Produto
from djangosige.apps.financeiro.models import Entrada, Saida, MovimentoCaixa
from djangosige.apps.gerencial.models import PagamentoFornecedor
from djangosige.apps.juridico.models import Processo, Prazo
from djangosige.apps.financeiro_grupo.models import TransferenciaGrupo
from djangosige.apps.contabilidade.models import (
    ProcessoContabil, Fiscal, ObrigacaoAcessoria, ApuracaoTributos)


class AgenteAdministrativoTestCase(BaseTestCase):

    def setUp(self):
        super(AgenteAdministrativoTestCase, self).setUp()
        self.hoje = date.today()
        # Comeca de uma base limpa nos modulos analisados
        Saida.objects.all().delete()
        Entrada.objects.all().delete()
        MovimentoCaixa.objects.all().delete()
        Produto.objects.update(estoque_minimo=0)
        agente.limpar_cache()

    def titulos(self, gravidade=None):
        return [a.titulo for a in agente.analisar(self.hoje)
                if gravidade is None or a.gravidade == gravidade]

    def test_sem_dados_nao_gera_alerta_financeiro(self):
        modulos = {a.modulo for a in agente.analisar(self.hoje)}
        self.assertNotIn('Financeiro', modulos)

    def test_contas_vencidas_e_risco_de_caixa(self):
        Saida.objects.create(descricao='Aluguel', valor_liquido=Decimal('1500.00'),
                             data_vencimento=self.hoje - timedelta(days=3), status='1')
        Saida.objects.create(descricao='Energia', valor_liquido=Decimal('400.00'),
                             data_vencimento=self.hoje + timedelta(days=2), status='1')
        Entrada.objects.create(descricao='Venda 10', valor_liquido=Decimal('300.00'),
                               data_vencimento=self.hoje - timedelta(days=1), status='2')
        MovimentoCaixa.objects.create(data_movimento=self.hoje - timedelta(days=1),
                                      saldo_final=Decimal('200.00'))

        alertas = agente.analisar(self.hoje)
        criticos = [a.titulo for a in alertas if a.gravidade == agente.CRITICO]
        self.assertIn('1 conta a pagar vencida', criticos)
        self.assertIn('1 conta a receber atrasada', criticos)
        self.assertIn('Risco de faltar caixa nos próximos dias', criticos)
        risco = next(a for a in alertas if a.titulo.startswith('Risco de faltar caixa'))
        # 1500 + 400 a pagar contra 200 de saldo (a entrada atrasada nao conta como prevista)
        self.assertEqual(risco.valor, Decimal('1700.00'))
        # Contas pagas nao entram
        Saida.objects.update(status='0')
        self.assertNotIn('1 conta a pagar vencida', self.titulos())

    def test_estoque_zerado_e_baixo(self):
        produtos = list(Produto.objects.all()[:2])
        if len(produtos) < 2:
            self.skipTest('fixture sem produtos suficientes')
        Produto.objects.filter(pk=produtos[0].pk).update(estoque_minimo=10, estoque_atual=0)
        Produto.objects.filter(pk=produtos[1].pk).update(estoque_minimo=10, estoque_atual=5)
        self.assertIn('1 produto sem estoque', self.titulos(agente.CRITICO))
        self.assertIn('1 produto abaixo do mínimo', self.titulos(agente.ATENCAO))

    def test_pagamento_fornecedor_vencido(self):
        fornecedor = Fornecedor.objects.first()
        PagamentoFornecedor.objects.create(
            fornecedor=fornecedor, descricao='NF 123', valor=Decimal('900.00'),
            data_emissao=self.hoje - timedelta(days=30), data_vencimento=self.hoje - timedelta(days=5))
        self.assertIn('1 pagamento a fornecedor vencido', self.titulos(agente.CRITICO))

    def test_prazo_juridico_proximo_e_risco_alto(self):
        processo = Processo.objects.create(
            numero='0001-TESTE', empresa=Empresa.objects.first(), descricao='Ação trabalhista',
            parte_contraria='Fulano', orgao='tst', tipo_processo='Trabalhista',
            valor_causa=Decimal('100000.00'), nivel_risco='alto', probabilidade_perda=40,
            data_distribuicao=self.hoje - timedelta(days=100))
        Prazo.objects.create(processo=processo, descricao='Contestação',
                             data_intimacao=self.hoje - timedelta(days=10),
                             data_vencimento=self.hoje + timedelta(days=2))
        alertas = agente.analisar(self.hoje)
        prazo = next(a for a in alertas if a.titulo == 'Prazo processual: Contestação')
        self.assertEqual(prazo.gravidade, agente.CRITICO)
        self.assertIn('0001-TESTE', prazo.detalhe)
        risco = next(a for a in alertas if a.titulo == '1 processo de risco alto')
        self.assertEqual(risco.valor, Decimal('40000.00'))
        # O alerta de prazo do processo nao se repete quando ha prazo cadastrado
        Processo.objects.filter(pk=processo.pk).update(proximo_prazo=self.hoje + timedelta(days=2))
        self.assertNotIn('Prazo do processo 0001-TESTE', self.titulos())

    def test_transferencia_parada(self):
        empresas = list(Empresa.objects.all()[:2])
        if len(empresas) < 2:
            self.skipTest('fixture sem duas empresas')
        TransferenciaGrupo.objects.create(
            empresa_origem=empresas[0], empresa_destino=empresas[1], valor=Decimal('5000.00'),
            finalidade='Capital de giro', data=timezone.now() - timedelta(days=6))
        self.assertIn('1 transferência pendente há mais de 3 dias', self.titulos(agente.ATENCAO))

    def test_obrigacao_e_tributo_da_contabilidade(self):
        processo = ProcessoContabil.objects.create(cliente=Cliente.objects.first(), numero_processo='PC-1')
        fiscal = Fiscal.objects.create(processo=processo, regime_tributario='simples')
        ObrigacaoAcessoria.objects.create(fiscal=fiscal, tipo='dctf', mes_referencia=1,
                                          ano_referencia=self.hoje.year,
                                          data_vencimento=self.hoje + timedelta(days=1))
        # Competência de dois meses atrás: o vencimento (dia 20 do mês seguinte) já
        # passou em qualquer dia do mês, então o alerta não depende da data do teste.
        anterior = (self.hoje.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
        ApuracaoTributos.objects.create(fiscal=fiscal, mes_referencia=anterior.month,
                                        ano_referencia=anterior.year, total_tributos=Decimal('820.00'))
        titulos = self.titulos()
        self.assertIn(f'DCTF 01/{self.hoje.year} não entregue', titulos)
        self.assertIn(f'Tributos de {anterior.month:02d}/{anterior.year} não pagos', titulos)

    def test_ordem_critico_primeiro(self):
        Saida.objects.create(descricao='X', valor_liquido=Decimal('10.00'),
                             data_vencimento=self.hoje + timedelta(days=3), status='1')
        Saida.objects.create(descricao='Y', valor_liquido=Decimal('10.00'),
                             data_vencimento=self.hoje - timedelta(days=3), status='1')
        gravidades = [agente.ORDEM_GRAVIDADE[a.gravidade] for a in agente.analisar(self.hoje)]
        self.assertEqual(gravidades, sorted(gravidades))

    def test_regra_com_erro_nao_derruba_o_resto(self):
        def quebrada(hoje):
            raise RuntimeError('tabela inexistente')
        original = list(agente.REGRAS)
        agente.REGRAS.insert(0, quebrada)
        try:
            Saida.objects.create(descricao='Z', valor_liquido=Decimal('10.00'),
                                 data_vencimento=self.hoje - timedelta(days=1), status='1')
            with self.assertLogs('djangosige.apps.base.agente', level='ERROR'):
                self.assertIn('1 conta a pagar vencida', self.titulos())
        finally:
            agente.REGRAS[:] = original

    def test_dashboard_e_pagina_de_alertas(self):
        Saida.objects.create(descricao='Aluguel', valor_liquido=Decimal('1500.00'),
                             data_vencimento=self.hoje - timedelta(days=3), status='1')
        response = self.client.get(reverse('base:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assistente administrativo')
        self.assertContains(response, '1 conta a pagar vencida')

        response = self.client.get(reverse('base:alertasview'), {'gravidade': 'critico'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1 conta a pagar vencida')
        self.assertTrue(all(a.gravidade == agente.CRITICO for a in response.context['alertas']))
        # Contador do topo
        self.assertGreaterEqual(response.context['agente_criticos'], 1)
