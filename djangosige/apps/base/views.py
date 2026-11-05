# -*- coding: utf-8 -*-

from django.views.generic import TemplateView
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F

from djangosige.apps.cadastro.models import Cliente, Fornecedor, Produto, Empresa, Transportadora
from djangosige.apps.vendas.models import OrcamentoVenda, PedidoVenda
from djangosige.apps.compras.models import OrcamentoCompra, PedidoCompra
from djangosige.apps.financeiro.models import MovimentoCaixa, Entrada, Saida
from djangosige.apps.base import agente

from datetime import datetime


def alertas_do_agente():
    # O dashboard sempre roda a analise na hora e renova o cache usado no topo
    agente.limpar_cache()
    return agente.alertas_em_cache()


class IndexView(TemplateView):
    template_name = 'base/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        quantidade_cadastro = {}
        agenda_hoje = {}
        alertas = {}
        data_atual = datetime.now().date()

        context['data_atual'] = data_atual.strftime('%d/%m/%Y')

        quantidade_cadastro['clientes'] = Cliente.objects.all().count()
        quantidade_cadastro['fornecedores'] = Fornecedor.objects.all().count()
        quantidade_cadastro['produtos'] = Produto.objects.all().count()
        quantidade_cadastro['empresas'] = Empresa.objects.all().count()
        quantidade_cadastro[
            'transportadoras'] = Transportadora.objects.all().count()
        context['quantidade_cadastro'] = quantidade_cadastro

        agenda_hoje['orcamento_venda_hoje'] = OrcamentoVenda.objects.filter(
            data_vencimento=data_atual, status='0').count()
        agenda_hoje['orcamento_compra_hoje'] = OrcamentoCompra.objects.filter(
            data_vencimento=data_atual, status='0').count()
        agenda_hoje['pedido_venda_hoje'] = PedidoVenda.objects.filter(
            data_entrega=data_atual, status='0').count()
        agenda_hoje['pedido_compra_hoje'] = PedidoCompra.objects.filter(
            data_entrega=data_atual, status='0').count()
        agenda_hoje['contas_receber_hoje'] = Entrada.objects.filter(
            data_vencimento=data_atual, status__in=['1', '2']).count()
        agenda_hoje['contas_pagar_hoje'] = Saida.objects.filter(
            data_vencimento=data_atual, status__in=['1', '2']).count()
        context['agenda_hoje'] = agenda_hoje

        alertas['produtos_baixo_estoque'] = Produto.objects.filter(
            estoque_atual__lte=F('estoque_minimo')).count()
        alertas['orcamentos_venda_vencidos'] = OrcamentoVenda.objects.filter(
            data_vencimento__lte=data_atual, status='0').count()
        alertas['pedidos_venda_atrasados'] = PedidoVenda.objects.filter(
            data_entrega__lte=data_atual, status='0').count()
        alertas['orcamentos_compra_vencidos'] = OrcamentoCompra.objects.filter(
            data_vencimento__lte=data_atual, status='0').count()
        alertas['pedidos_compra_atrasados'] = PedidoCompra.objects.filter(
            data_entrega__lte=data_atual, status='0').count()
        alertas['contas_receber_atrasadas'] = Entrada.objects.filter(
            data_vencimento__lte=data_atual, status__in=['1', '2']).count()
        alertas['contas_pagar_atrasadas'] = Saida.objects.filter(
            data_vencimento__lte=data_atual, status__in=['1', '2']).count()
        context['alertas'] = alertas

        try:
            context['movimento_dia'] = MovimentoCaixa.objects.get(
                data_movimento=data_atual)
        except (MovimentoCaixa.DoesNotExist, ObjectDoesNotExist):
            ultimo_mvmt = MovimentoCaixa.objects.filter(
                data_movimento__lt=data_atual)
            if ultimo_mvmt:
                context['saldo'] = ultimo_mvmt.latest(
                    'data_movimento').saldo_final
            else:
                context['saldo'] = '0,00'

        alertas_agente = alertas_do_agente()
        context['agente_alertas'] = alertas_agente[:8]
        context['agente_total'] = len(alertas_agente)
        context['agente_resumo'] = agente.contar(alertas_agente)

        return context


class AlertasView(TemplateView):
    template_name = 'base/alertas.html'

    def get_context_data(self, **kwargs):
        context = super(AlertasView, self).get_context_data(**kwargs)
        alertas = alertas_do_agente()
        context['agente_resumo'] = agente.contar(alertas)
        context['modulos'] = sorted({a.modulo for a in alertas})

        gravidade = self.request.GET.get('gravidade')
        modulo = self.request.GET.get('modulo')
        if gravidade:
            alertas = [a for a in alertas if a.gravidade == gravidade]
        if modulo:
            alertas = [a for a in alertas if a.modulo == modulo]
        context['alertas'] = alertas
        context['filtro_gravidade'] = gravidade or ''
        context['filtro_modulo'] = modulo or ''
        context['data_atual'] = datetime.now().strftime('%d/%m/%Y')
        return context


class ImportacaoView(TemplateView):
    template_name = 'base/importacao.html'

    TIPOS = {
        'planilha': {
            'titulo': 'Planilha de pagamentos',
            'descricao': 'Lança pagamentos a fornecedores no controle gerencial a partir de um arquivo CSV ou Excel.',
            'url': 'gerencial:importar_planilha',
            'campo': 'arquivo',
            'aceita': '.csv,.xlsx,.xls',
            'formatos': 'CSV (separado por ponto e vírgula), XLSX ou XLS',
        },
        'nfe-entrada': {
            'titulo': 'NF-e de entrada',
            'descricao': 'Cadastra uma nota fiscal recebida de fornecedor a partir do arquivo XML.',
            'url': 'fiscal:importarnotafiscalentrada',
            'campo': 'arquivo_xml',
            'aceita': '.xml,text/xml',
            'formatos': 'XML da NF-e enviado pelo fornecedor',
            'fornecedor': True,
        },
        'nfe-saida': {
            'titulo': 'NF-e de saída',
            'descricao': 'Cadastra uma nota fiscal emitida em outro sistema a partir do arquivo XML.',
            'url': 'fiscal:importarnotafiscalsaida',
            'campo': 'arquivo_xml',
            'aceita': '.xml,text/xml',
            'formatos': 'XML da NF-e emitida pela empresa',
        },
    }

    def get_context_data(self, **kwargs):
        from django.http import Http404
        from djangosige.apps.gerencial.models import ImportacaoPlanilha

        context = super(ImportacaoView, self).get_context_data(**kwargs)
        tipo = kwargs.get('tipo')
        if tipo not in self.TIPOS:
            raise Http404
        context['tipo'] = tipo
        context['importacao'] = self.TIPOS[tipo]
        if tipo == 'planilha':
            context['historico'] = ImportacaoPlanilha.objects.select_related('usuario')[:10]
        return context


def handler404(request):
    response = render(request, '404.html', {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response
