from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from djangosige.apps.cadastro.models import Cliente
from djangosige.apps.contabilidade.models import (
    ApuracaoTributos, Contabil, ConciliacaoBancaria, DemonstracaoResultado, Fiscal,
    LancamentoContabil, ObrigacaoAcessoria, ProcessoContabil)


class TelasContabilidadeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('contab_telas', 'c@t.com', 'senha-teste')
        self.client.force_login(self.user)
        cliente = Cliente.objects.create(nome_razao_social='Cliente Contábil', tipo_pessoa='PJ')
        self.processo = ProcessoContabil.objects.create(cliente=cliente, numero_processo='PC-T1', responsavel=self.user)
        self.fiscal = Fiscal.objects.create(processo=self.processo)
        self.contabil = Contabil.objects.create(processo=self.processo)
        ApuracaoTributos.objects.create(fiscal=self.fiscal, mes_referencia=3, ano_referencia=2026,
                                        receita_bruta=Decimal('150000.00'), total_tributos=Decimal('12345.67'))
        ObrigacaoAcessoria.objects.create(fiscal=self.fiscal, tipo=ObrigacaoAcessoria._meta.get_field('tipo').choices[0][0],
                                          mes_referencia=3, ano_referencia=2026, data_vencimento=date(2026, 4, 20))
        LancamentoContabil.objects.create(contabil=self.contabil, data_lancamento=date(2026, 3, 5), numero_lancamento='L-1',
                                          tipo='debito', conta_debito='1.1.01', conta_credito='2.1.01', valor=Decimal('9876.54'),
                                          historico='Pagamento de fornecedor', usuario=self.user)
        ConciliacaoBancaria.objects.create(contabil=self.contabil, mes_referencia=3, ano_referencia=2026, banco='Banco X',
                                           agencia='0001', conta='123-4', saldo_inicial=Decimal('1000'),
                                           saldo_final=Decimal('2500.50'), saldo_extrato=Decimal('2500.50'))
        DemonstracaoResultado.objects.create(contabil=self.contabil, mes_referencia=3, ano_referencia=2026,
                                             receita_bruta=Decimal('150000'), lucro_liquido=Decimal('-1234.56'))

    def test_telas_abrem_com_valores_no_padrao_brasileiro(self):
        casos = [
            (reverse('contabilidade:apuracao_tributos', args=[self.fiscal.pk]), 'R$ 12.345,67'),
            (reverse('contabilidade:obrigacoes_acessorias', args=[self.fiscal.pk]), '20/04/2026'),
            (reverse('contabilidade:lancamentos_contabeis', args=[self.contabil.pk]), 'R$ 9.876,54'),
            (reverse('contabilidade:conciliacao_bancaria', args=[self.contabil.pk]), 'R$ 2.500,50'),
            (reverse('contabilidade:demonstracao_resultado', args=[self.contabil.pk]), '-R$ 1.234,56'),
            (reverse('contabilidade:editar_processo', args=[self.processo.pk]), 'Salvar alterações'),
        ]
        for url, texto in casos:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, texto)

    def test_etapas_levam_as_consultas(self):
        self.assertContains(self.client.get(reverse('contabilidade:fiscal', args=[self.processo.pk])),
                            reverse('contabilidade:apuracao_tributos', args=[self.fiscal.pk]))
        self.assertContains(self.client.get(reverse('contabilidade:contabil', args=[self.processo.pk])),
                            reverse('contabilidade:demonstracao_resultado', args=[self.contabil.pk]))
        self.assertContains(self.client.get(reverse('contabilidade:detalhe_processo', args=[self.processo.pk])),
                            reverse('contabilidade:editar_processo', args=[self.processo.pk]))
