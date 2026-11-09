# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from djangosige.apps.canais import baselinker
from djangosige.apps.canais.baselinker import comissao_e_frete, sincronizar
from djangosige.apps.canais.models import (ContaCanal, CustoProdutoBase, PedidoCanal, ResumoDiarioCanal,
                                           SincronizacaoBase)

ONTEM = timezone.localdate() - timedelta(days=1)
T = int(timezone.make_aware(datetime.combine(ONTEM, datetime.min.time())).timestamp()) + 12 * 3600


def pedido(order_id, fonte, source_id, status, preco, qtd=1, frete=0, comentario='', produto='111', segundos=0):
    return {'order_id': order_id, 'order_source': fonte, 'order_source_id': source_id, 'order_status_id': status,
            'date_add': T + segundos, 'date_confirmed': T + segundos, 'delivery_price': frete,
            'admin_comments': comentario,
            'products': [{'storage': 'db', 'storage_id': 44979, 'product_id': produto, 'variant_id': '0',
                          'price_brutto': preco, 'quantity': qtd}]}


class ClienteFalso(object):
    def __init__(self, pedidos, devolucoes=(), custos=None, erro=None):
        self.pedidos, self.devolucoes = list(pedidos), list(devolucoes)
        self.custos = custos or {}
        self.erro = erro
        self.chamadas = 0
        self.log = []

    def chamar(self, metodo, parametros=None):
        self.chamadas += 1
        self.log.append((metodo, parametros))
        if self.erro:
            raise baselinker.ErroBase(self.erro)
        if metodo == 'getOrderStatusList':
            return {'statuses': [{'id': 1, 'name': 'Novos pedidos'}, {'id': 9, 'name': 'Cancelado'}]}
        if metodo == 'getOrderSources':
            return {'sources': {'melibr': {'28102': 'ML - Led Tools'}, 'shopeebr': {'27932': 'Shopee Led'},
                                'order_return': ['Devolução']}}
        if metodo == 'getOrders':
            lista = [p for p in self.pedidos if p['date_confirmed'] >= parametros['date_confirmed_from']]
            if 'status_id' in parametros:
                lista = [p for p in lista if p['order_status_id'] == parametros['status_id']]
            return {'orders': sorted(lista, key=lambda p: p['date_confirmed'])[:100]}
        if metodo == 'getOrderReturns':
            return {'returns': [r for r in self.devolucoes if r['date_add'] >= parametros['date_from']][:100]}
        if metodo == 'getInventoryProductsData':
            return {'products': {str(i): {'average_cost': self.custos.get(str(i), 0)} for i in parametros['products']}}
        raise AssertionError(metodo)


class SincronizacaoTests(TestCase):
    def setUp(self):
        baselinker.INTERVALO_ENTRE_CHAMADAS = 0

    def test_le_comissao_e_frete_do_mercado_livre(self):
        comissao, frete = comissao_e_frete(
            'comissão sobre venda dos produtos: 6.00 comissão sobre venda dos produtos: 16.92 cross_docking '
            'comissão sobre venda dos produtos: 24.39 Frete pago pelo vendedor: -78.45 Frete de: (BR)')
        self.assertEqual(comissao, Decimal('47.31'))
        self.assertEqual(frete, Decimal('78.45'))
        self.assertEqual(comissao_e_frete('Data de entrega: 10/11'), (None, None))

    def test_sincroniza_pedidos_custos_cancelamentos_e_devolucoes(self):
        cliente = ClienteFalso([
            pedido(1, 'melibr', 28102, 1, 100, qtd=2, comentario='comissão sobre venda dos produtos: 30.00 Frete pago pelo vendedor: -20.00'),
            pedido(2, 'shopeebr', 27932, 1, 50, frete=10, produto='222', segundos=5),
            pedido(3, 'shopeebr', 27932, 9, 80, produto='222', segundos=9),
        ], devolucoes=[{'return_id': 7, 'order_id': 1, 'order_return_source': 'melibr', 'order_return_source_id': 28102,
                        'date_add': T + 60, 'products': [{'price_brutto': 100, 'quantity': 1}]}],
            custos={'111': 40, '222': 0})
        registro = sincronizar(cliente=cliente)
        self.assertTrue(registro.completa, registro.erro)
        self.assertEqual(PedidoCanal.objects.count(), 3)
        self.assertTrue(PedidoCanal.objects.get(pk=3).cancelado)
        self.assertEqual(PedidoCanal.objects.get(pk=1).custo, Decimal('80.00'))
        self.assertFalse(PedidoCanal.objects.get(pk=2).custo_completo)  # custo zero no Base
        self.assertEqual(CustoProdutoBase.objects.get(chave='44979:111').custo, Decimal('40.00'))

        ml = ResumoDiarioCanal.objects.get(data=ONTEM, conta_id=28102)
        self.assertEqual((ml.pedidos, ml.vendas_brutas, ml.comissao_informada, ml.frete_vendedor, ml.devolucoes_qtd),
                         (1, Decimal('200.00'), Decimal('30.00'), Decimal('20.00'), 1))
        shopee = ResumoDiarioCanal.objects.get(data=ONTEM, conta_id=27932)
        self.assertEqual((shopee.pedidos, shopee.vendas_brutas, shopee.cancelados_qtd, shopee.cancelados_valor,
                          shopee.base_sem_comissao, shopee.pedidos_sem_custo),
                         (2, Decimal('140.00'), 1, Decimal('80.00'), Decimal('50.00'), 1))

        # Segunda vez: o pedido 2 foi cancelado no Base; o resumo é refeito.
        cliente.pedidos[1]['order_status_id'] = 9
        sincronizar(cliente=cliente)
        self.assertEqual(PedidoCanal.objects.count(), 3)
        self.assertEqual(ResumoDiarioCanal.objects.get(data=ONTEM, conta_id=27932).cancelados_qtd, 2)

    def test_paginacao_de_100_em_100(self):
        cliente = ClienteFalso([pedido(i, 'melibr', 28102, 1, 10, segundos=i) for i in range(1, 251)])
        sincronizar(cliente=cliente)
        self.assertEqual(PedidoCanal.objects.count(), 250)
        self.assertEqual(ResumoDiarioCanal.objects.get(data=ONTEM).pedidos, 250)

    def test_erro_da_api_fica_registrado(self):
        registro = sincronizar(cliente=ClienteFalso([], erro='Base.com: token inválido'))
        self.assertFalse(registro.completa)
        self.assertIn('token inválido', registro.erro)

    @override_settings(BASELINKER_TOKEN='')
    def test_sem_token_avisa(self):
        registro = sincronizar()
        self.assertIn('BASELINKER_TOKEN', registro.erro)


class TelasCanaisTests(TestCase):
    def setUp(self):
        baselinker.INTERVALO_ENTRE_CHAMADAS = 0
        self.user = get_user_model().objects.create_superuser('canais', 'c@t.com', 'senha-de-teste')
        self.client.force_login(self.user)

    def test_painel_vazio_sem_token(self):
        with self.settings(BASELINKER_TOKEN=''):
            response = self.client.get(reverse('canais:painel'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Falta o token da API do Base.com')
        self.assertContains(response, 'Ainda não há pedidos')

    def test_painel_com_metricas_e_comissao_estimada(self):
        sincronizar(cliente=ClienteFalso([
            pedido(1, 'melibr', 28102, 1, 100, comentario='comissão sobre venda dos produtos: 15.00 Frete pago pelo vendedor: -5.00'),
            pedido(2, 'shopeebr', 27932, 1, 200, produto='222', segundos=3),
        ], custos={'111': 40, '222': 100}))
        ContaCanal.objects.filter(pk=27932).update(comissao_percentual=Decimal('20'))
        response = self.client.get(reverse('canais:painel'))
        atual = response.context['atual']
        self.assertEqual(atual['vendas_brutas'], Decimal('300.00'))
        self.assertEqual(atual['comissao'], Decimal('55.00'))  # 15 informado + 20% de 200
        self.assertEqual(atual['margem'], Decimal('300.00') - 140 - 55 - 5)
        self.assertContains(response, 'ML - Led Tools')
        self.assertContains(response, 'Shopee Led')

    def test_salvar_comissoes(self):
        ContaCanal.objects.create(source_id=27932, origem='shopeebr', nome='Shopee Led')
        response = self.client.post(reverse('canais:contas'), {'pct_27932': '18,5'})
        self.assertRedirects(response, reverse('canais:painel'))
        self.assertEqual(ContaCanal.objects.get().comissao_percentual, Decimal('18.5'))
        response = self.client.post(reverse('canais:contas'), {'pct_27932': '150'})
        self.assertContains(response, 'entre 0 e 100')

    def test_periodo_personalizado_e_mes_passado_abrem(self):
        for params in ({'periodo': 'personalizado', 'de': '2026-10-01', 'ate': '2026-10-31'},
                       {'periodo': 'mes_anterior'}, {'periodo': '30'}, {'periodo': 'mes'}):
            self.assertEqual(self.client.get(reverse('canais:painel'), params).status_code, 200)

    def test_comando_existe(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.settings(BASELINKER_TOKEN=''):
            with self.assertRaises(CommandError):
                call_command('sincronizar_base', '--desde', '2026-10-01', stdout=open('/dev/null', 'w'))
        self.assertTrue(SincronizacaoBase.objects.exists())
