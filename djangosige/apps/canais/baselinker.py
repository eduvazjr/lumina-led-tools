# -*- coding: utf-8 -*-
"""Sincronização com a API do Base.com (BaseLinker).

    sincronizar()            busca o que mudou desde a última vez
    sincronizar(desde=data)  busca tudo a partir de uma data (carga inicial)

A API aceita até 100 chamadas por minuto; cada chamada traz no máximo 100
pedidos. O token vem de BASELINKER_TOKEN (arquivo .env do servidor).
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (ContaCanal, CustoProdutoBase, DevolucaoCanal, PedidoCanal, ResumoDiarioCanal,
                     SincronizacaoBase, StatusPedidoBase)

URL_API = 'https://api.baselinker.com/connector.php'
INTERVALO_ENTRE_CHAMADAS = 0.65   # segundos: fica abaixo do limite de 100 por minuto
DIAS_CARGA_INICIAL = 35          # primeira sincronização: últimas 5 semanas
DIAS_DETALHE = 90                # pedidos guardados um a um; depois disso só o resumo diário
DIAS_REVER_CANCELAMENTOS = 15    # pedidos cancelados depois de confirmados
DIAS_CUSTO_VALIDO = 7            # custo médio do produto é consultado de novo depois disso

RE_COMISSAO = re.compile(r'comiss[ãa]o sobre venda dos produtos:\s*(-?[\d.,]+)', re.IGNORECASE)
RE_FRETE_VENDEDOR = re.compile(r'frete pago pelo vendedor:\s*(-?[\d.,]+)', re.IGNORECASE)


class ErroBase(Exception):
    pass


class LimiteDeChamadas(Exception):
    """A sincronização parou no limite combinado; continua na próxima."""


class ClienteBase(object):
    def __init__(self, token=None, limite_chamadas=None):
        self.token = token if token is not None else getattr(settings, 'BASELINKER_TOKEN', '')
        self.limite_chamadas = limite_chamadas
        self.chamadas = 0
        self._ultima = 0.0

    def chamar(self, metodo, parametros=None):
        if not self.token:
            raise ErroBase('O token da API do Base.com não está configurado (BASELINKER_TOKEN).')
        if self.limite_chamadas is not None and self.chamadas >= self.limite_chamadas:
            raise LimiteDeChamadas()
        espera = INTERVALO_ENTRE_CHAMADAS - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)
        corpo = urllib.parse.urlencode({
            'method': metodo, 'parameters': json.dumps(parametros or {})}).encode('utf-8')
        pedido = urllib.request.Request(URL_API, data=corpo, headers={'X-BLToken': self.token})
        self._ultima = time.monotonic()
        self.chamadas += 1
        try:
            with urllib.request.urlopen(pedido, timeout=60) as resposta:
                dados = json.loads(resposta.read().decode('utf-8'))
        except urllib.error.HTTPError as erro:
            raise ErroBase('O Base.com respondeu com erro %s.' % erro.code)
        except (urllib.error.URLError, OSError) as erro:
            raise ErroBase('Não foi possível falar com o Base.com (%s). No plano gratuito do '
                           'PythonAnywhere o endereço api.baselinker.com precisa estar liberado.'
                           % getattr(erro, 'reason', erro))
        except ValueError:
            raise ErroBase('O Base.com devolveu uma resposta que não deu para ler.')
        if dados.get('status') != 'SUCCESS':
            raise ErroBase('Base.com: %s' % (dados.get('error_message') or dados.get('error_code') or 'erro'))
        return dados


# ------------------------------------------------------------------ apoio

def _dec(valor):
    try:
        return Decimal(str(valor or 0)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return Decimal('0.00')


def _numero_texto(texto):
    """'16.92' (como o Base escreve nos comentários) ou '1.234,56'."""
    texto = texto.strip().rstrip('.,')
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    return _dec(texto)


def comissao_e_frete(comentario):
    """Comissão e frete pago pelo vendedor escritos pelo Mercado Livre no pedido."""
    comentario = comentario or ''
    comissoes = [_numero_texto(v) for v in RE_COMISSAO.findall(comentario)]
    fretes = [abs(_numero_texto(v)) for v in RE_FRETE_VENDEDOR.findall(comentario)]
    return (sum(comissoes, Decimal('0.00')) if comissoes else None,
            sum(fretes, Decimal('0.00')) if fretes else None)


def _data_local(unix):
    return timezone.localtime(datetime.fromtimestamp(int(unix or 0), tz=dt_timezone.utc)).date()


def _unix(data):
    meia_noite = timezone.make_aware(datetime.combine(data, datetime.min.time()))
    return int(meia_noite.timestamp())


def _chave_custo(produto):
    if produto.get('storage') != 'db' or not produto.get('storage_id'):
        return None
    variacao = str(produto.get('variant_id') or '0')
    item = variacao if variacao not in ('0', '') else str(produto.get('product_id') or '')
    if not item.isdigit():
        return None
    return '%s:%s' % (produto['storage_id'], item)


# ------------------------------------------------------------------ sincronização

class Sincronizador(object):
    def __init__(self, cliente):
        self.cliente = cliente
        self.contas = {}
        self.cancelados = set()
        self.custos = {}
        self.datas = set()
        self.pedidos = 0
        self.devolucoes = 0

    # cadastros -------------------------------------------------------------
    def carregar_cadastros(self):
        for status in self.cliente.chamar('getOrderStatusList').get('statuses', []):
            obj, _ = StatusPedidoBase.objects.update_or_create(
                status_id=status['id'], defaults={'nome': status.get('name', '')[:120],
                                                  'cancelado': 'cancel' in status.get('name', '').lower()})
        self.cancelados = set(StatusPedidoBase.objects.filter(cancelado=True).values_list('status_id', flat=True))
        fontes = self.cliente.chamar('getOrderSources').get('sources', {})
        for origem, contas in fontes.items():
            if not isinstance(contas, dict):
                continue
            for source_id, nome in contas.items():
                if str(source_id).isdigit():
                    ContaCanal.objects.update_or_create(
                        source_id=int(source_id), defaults={'origem': origem[:30], 'nome': str(nome)[:120]})
        self.contas = {c.source_id: c for c in ContaCanal.objects.all()}

    def _conta(self, origem, source_id):
        source_id = int(source_id or 0)
        if source_id not in self.contas:
            self.contas[source_id] = ContaCanal.objects.create(
                source_id=source_id, origem=(origem or '')[:30], nome=('%s %s' % (origem, source_id))[:120])
        return self.contas[source_id]

    # custos ----------------------------------------------------------------
    def garantir_custos(self, chaves):
        faltando = set(chaves) - set(self.custos)
        if not faltando:
            return
        validade = timezone.now() - timedelta(days=DIAS_CUSTO_VALIDO)
        for c in CustoProdutoBase.objects.filter(chave__in=faltando, atualizado_em__gte=validade):
            self.custos[c.chave] = c.custo
        faltando -= set(self.custos)
        por_inventario = defaultdict(list)
        for chave in faltando:
            inventario, item = chave.split(':')
            por_inventario[inventario].append(int(item))
        for inventario, itens in por_inventario.items():
            for i in range(0, len(itens), 100):
                lote = itens[i:i + 100]
                produtos = self.cliente.chamar('getInventoryProductsData', {
                    'inventory_id': int(inventario), 'products': lote}).get('products', {}) or {}
                for item in lote:
                    chave = '%s:%s' % (inventario, item)
                    custo = _dec((produtos.get(str(item)) or {}).get('average_cost'))
                    self.custos[chave] = custo
                    CustoProdutoBase.objects.update_or_create(chave=chave, defaults={'custo': custo})

    # pedidos ---------------------------------------------------------------
    def salvar_pedidos(self, pedidos):
        chaves = {_chave_custo(p) for o in pedidos for p in o.get('products', [])} - {None}
        self.garantir_custos(chaves)
        novos = []
        for o in pedidos:
            produtos = o.get('products', [])
            valor = sum((_dec(p.get('price_brutto')) * int(p.get('quantity') or 0) for p in produtos), Decimal('0.00'))
            custo, completo = Decimal('0.00'), True
            for p in produtos:
                unitario = self.custos.get(_chave_custo(p))
                if not unitario:
                    completo = False
                else:
                    custo += unitario * int(p.get('quantity') or 0)
            comissao, frete_vendedor = comissao_e_frete(o.get('admin_comments'))
            data = _data_local(o.get('date_add') or o.get('date_confirmed'))
            novos.append(PedidoCanal(
                order_id=o['order_id'], conta=self._conta(o.get('order_source'), o.get('order_source_id')),
                status_id=int(o.get('order_status_id') or 0), data=data,
                confirmado_em=int(o.get('date_confirmed') or 0), valor_produtos=valor,
                frete_cliente=_dec(o.get('delivery_price')), comissao=comissao, frete_vendedor=frete_vendedor,
                custo=custo, custo_completo=completo,
                unidades=sum(int(p.get('quantity') or 0) for p in produtos),
                cancelado=int(o.get('order_status_id') or 0) in self.cancelados))
            self.datas.add(data)
        existentes = set(PedidoCanal.objects.filter(pk__in=[p.order_id for p in novos]).values_list('pk', flat=True))
        for antigo in PedidoCanal.objects.filter(pk__in=existentes).only('data'):
            self.datas.add(antigo.data)  # se o pedido mudou de dia, o dia antigo também é refeito
        campos = ['conta', 'status_id', 'data', 'confirmado_em', 'valor_produtos', 'frete_cliente', 'comissao',
                  'frete_vendedor', 'custo', 'custo_completo', 'unidades', 'cancelado']
        with transaction.atomic():
            PedidoCanal.objects.bulk_create([p for p in novos if p.order_id not in existentes])
            PedidoCanal.objects.bulk_update([p for p in novos if p.order_id in existentes], campos)
        self.pedidos += len(novos)

    def buscar_pedidos(self, desde_unix, extra=None):
        cursor = desde_unix
        while True:
            parametros = {'date_confirmed_from': cursor, 'get_unconfirmed_orders': False}
            parametros.update(extra or {})
            pagina = self.cliente.chamar('getOrders', parametros).get('orders', [])
            if pagina:
                self.salvar_pedidos(pagina)
            if len(pagina) < 100:
                return
            ultimo = max(int(o.get('date_confirmed') or 0) for o in pagina)
            cursor = ultimo if ultimo > cursor else cursor + 1

    # devoluções ------------------------------------------------------------
    def buscar_devolucoes(self, desde_unix):
        cursor = desde_unix
        while True:
            pagina = self.cliente.chamar('getOrderReturns', {'date_from': cursor}).get('returns', [])
            for r in pagina:
                data = _data_local(r.get('date_add'))
                DevolucaoCanal.objects.update_or_create(return_id=r['return_id'], defaults={
                    'order_id': int(r.get('order_id') or 0),
                    'conta': self._conta(r.get('order_return_source'), r.get('order_return_source_id')),
                    'data': data, 'criada_em': int(r.get('date_add') or 0),
                    'valor': sum((_dec(p.get('price_brutto')) * int(p.get('quantity') or 0)
                                  for p in r.get('products', [])), Decimal('0.00'))})
                self.datas.add(data)
            self.devolucoes += len(pagina)
            if len(pagina) < 100:
                return
            ultimo = max(int(r.get('date_add') or 0) for r in pagina)
            cursor = ultimo if ultimo > cursor else cursor + 1


def refazer_resumos(datas):
    """Recalcula o resumo diário a partir dos pedidos guardados. Dias além do
    período guardado em detalhe ficam como estão."""
    limite = timezone.localdate() - timedelta(days=DIAS_DETALHE - 1)
    for data in sorted(d for d in datas if d >= limite):
        linhas = defaultdict(lambda: defaultdict(Decimal))
        for p in PedidoCanal.objects.filter(data=data):
            r = linhas[p.conta_id]
            bruto = p.valor_produtos + p.frete_cliente
            r['pedidos'] += 1
            r['unidades'] += p.unidades
            r['vendas_brutas'] += bruto
            r['frete_cliente'] += p.frete_cliente
            if p.cancelado:
                r['cancelados_qtd'] += 1
                r['cancelados_valor'] += bruto
                continue
            if p.comissao is None:
                r['base_sem_comissao'] += p.valor_produtos
            else:
                r['comissao_informada'] += p.comissao
            r['frete_vendedor'] += p.frete_vendedor or 0
            r['custo'] += p.custo
            if not p.custo_completo:
                r['pedidos_sem_custo'] += 1
        for d in DevolucaoCanal.objects.filter(data=data):
            linhas[d.conta_id]['devolucoes_qtd'] += 1
            linhas[d.conta_id]['devolucoes_valor'] += d.valor
        inteiros = ('pedidos', 'unidades', 'cancelados_qtd', 'devolucoes_qtd', 'pedidos_sem_custo')
        with transaction.atomic():
            ResumoDiarioCanal.objects.filter(data=data).delete()
            ResumoDiarioCanal.objects.bulk_create([
                ResumoDiarioCanal(data=data, conta_id=conta_id, **{
                    k: (int(v) if k in inteiros else v) for k, v in valores.items()})
                for conta_id, valores in linhas.items()])


def sincronizar(desde=None, limite_chamadas=None, cliente=None):
    """Busca pedidos e devoluções no Base.com e atualiza os resumos.

    desde: data inicial (carga inicial ou para refazer um período). Sem ela,
    continua de onde a última sincronização parou, revendo os 2 últimos dias.
    limite_chamadas: para a sincronização feita pelo botão da tela, que não
    pode demorar; o que faltar fica para a próxima.
    """
    cliente = cliente or ClienteBase(limite_chamadas=limite_chamadas)
    registro = SincronizacaoBase.objects.create()
    s = Sincronizador(cliente)
    hoje = timezone.localdate()
    try:
        s.carregar_cadastros()
        if desde:
            inicio = _unix(desde)
        else:
            ultimo = PedidoCanal.objects.order_by('-confirmado_em').values_list('confirmado_em', flat=True).first()
            inicio = (ultimo - 2 * 86400) if ultimo else _unix(hoje - timedelta(days=DIAS_CARGA_INICIAL))
        s.buscar_pedidos(inicio)
        if s.cancelados:
            revisao = max(min(inicio, _unix(hoje - timedelta(days=DIAS_REVER_CANCELAMENTOS))),
                          _unix(hoje - timedelta(days=DIAS_DETALHE - 1)))
            for status_id in sorted(s.cancelados):
                s.buscar_pedidos(revisao, {'status_id': status_id})
        ultima_devolucao = DevolucaoCanal.objects.order_by('-criada_em').values_list('criada_em', flat=True).first()
        s.buscar_devolucoes(_unix(desde) if desde else (ultima_devolucao + 1 if ultima_devolucao else inicio))
        registro.completa = True
    except LimiteDeChamadas:
        registro.erro = 'Parou no limite de chamadas desta vez; o restante vem na próxima sincronização.'
    except ErroBase as erro:
        registro.erro = str(erro)
    finally:
        refazer_resumos(s.datas)
        corte = hoje - timedelta(days=DIAS_DETALHE)
        PedidoCanal.objects.filter(data__lt=corte).delete()
        DevolucaoCanal.objects.filter(data__lt=corte).delete()
        registro.pedidos, registro.devolucoes, registro.chamadas = s.pedidos, s.devolucoes, cliente.chamadas
        registro.terminada_em = timezone.now()
        registro.save()
    return registro
