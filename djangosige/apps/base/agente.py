# -*- coding: utf-8 -*-
"""
Agente administrativo: le os dados de todos os modulos e gera alertas de
prazos e riscos para o dashboard.

Cada regra e uma funcao que recebe o dia de hoje e devolve uma lista de
Alerta. Uma regra que falhar (tabela ainda nao migrada, por exemplo) e
ignorada para nao derrubar o dashboard.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum, Count, F, Q
from django.urls import reverse

logger = logging.getLogger(__name__)

CRITICO = 'critico'
ATENCAO = 'atencao'
INFO = 'info'
ORDEM_GRAVIDADE = {CRITICO: 0, ATENCAO: 1, INFO: 2}

# Janela usada para "vence em breve"
DIAS_PROXIMOS = 7
CACHE_KEY = 'agente_administrativo_alertas'
CACHE_SEGUNDOS = 120


@dataclass
class Alerta:
    gravidade: str
    modulo: str
    titulo: str
    detalhe: str = ''
    url: str = ''
    valor: Decimal = None
    prazo: date = None

    @property
    def dias(self):
        if self.prazo is None:
            return None
        return (self.prazo - date.today()).days


def moeda(valor):
    valor = valor or 0
    texto = f'{valor:,.2f}'
    return 'R$ ' + texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def plural(n, singular, plural_):
    return f'{n} {singular if n == 1 else plural_}'


def quando(prazo, hoje):
    dias = (prazo - hoje).days
    if dias < 0:
        return f'venceu há {plural(-dias, "dia", "dias")}'
    if dias == 0:
        return 'vence hoje'
    if dias == 1:
        return 'vence amanhã'
    return f'vence em {dias} dias ({prazo:%d/%m})'


# ---------------------------------------------------------------- Financeiro

def regras_financeiro(hoje):
    from djangosige.apps.financeiro.models import Entrada, Saida, MovimentoCaixa

    alertas = []
    limite = hoje + timedelta(days=DIAS_PROXIMOS)
    abertas = Q(status__in=['1', '2'])

    def resumo(model, filtro):
        r = model.objects.filter(abertas, filtro).aggregate(
            n=Count('id'), total=Sum('valor_liquido'))
        return r['n'], r['total'] or Decimal(0)

    n, total = resumo(Saida, Q(data_vencimento__lt=hoje))
    if n:
        alertas.append(Alerta(CRITICO, 'Financeiro', f'{plural(n, "conta a pagar vencida", "contas a pagar vencidas")}',
                              f'{moeda(total)} em atraso. Juros e multa podem estar correndo.',
                              reverse('financeiro:listacontapagaratrasadasview'), total))
    n, total = resumo(Entrada, Q(data_vencimento__lt=hoje))
    if n:
        alertas.append(Alerta(CRITICO, 'Financeiro', f'{plural(n, "conta a receber atrasada", "contas a receber atrasadas")}',
                              f'{moeda(total)} que os clientes ainda não pagaram. Vale cobrar.',
                              reverse('financeiro:listacontareceberatrasadasview'), total))
    n, total = resumo(Saida, Q(data_vencimento=hoje))
    if n:
        alertas.append(Alerta(ATENCAO, 'Financeiro', f'{plural(n, "conta a pagar vence", "contas a pagar vencem")} hoje',
                              f'Total de {moeda(total)}.',
                              reverse('financeiro:listacontapagarhojeview'), total, hoje))
    n_pagar, total_pagar = resumo(Saida, Q(data_vencimento__gt=hoje, data_vencimento__lte=limite))
    if n_pagar:
        alertas.append(Alerta(INFO, 'Financeiro', f'{plural(n_pagar, "conta a pagar", "contas a pagar")} nos próximos {DIAS_PROXIMOS} dias',
                              f'Total de {moeda(total_pagar)}.',
                              reverse('financeiro:listacontapagarview'), total_pagar))
    n, total = resumo(Entrada, Q(data_vencimento__gte=hoje, data_vencimento__lte=limite))
    if n:
        alertas.append(Alerta(INFO, 'Financeiro', f'{plural(n, "recebimento previsto", "recebimentos previstos")} nos próximos {DIAS_PROXIMOS} dias',
                              f'Total de {moeda(total)}.',
                              reverse('financeiro:listacontareceberview'), total))

    # Risco de caixa: o que vence ate o fim da janela (incluindo atrasos)
    # contra o saldo atual mais o que deve entrar no mesmo periodo
    ultimo = MovimentoCaixa.objects.filter(
        data_movimento__lte=hoje).order_by('-data_movimento').first()
    if ultimo is not None:
        _, a_pagar = resumo(Saida, Q(data_vencimento__lte=limite))
        _, a_receber = resumo(Entrada, Q(data_vencimento__gte=hoje, data_vencimento__lte=limite))
        disponivel = (ultimo.saldo_final or 0) + a_receber
        if a_pagar > disponivel:
            falta = a_pagar - disponivel
            alertas.append(Alerta(CRITICO, 'Financeiro', 'Risco de faltar caixa nos próximos dias',
                                  f'Saldo de {moeda(ultimo.saldo_final)} mais {moeda(a_receber)} a receber não cobrem '
                                  f'{moeda(a_pagar)} a pagar até {limite:%d/%m}. Faltam {moeda(falta)}.',
                                  reverse('financeiro:fluxodecaixaview'), falta))
    return alertas


# ------------------------------------------------------- Vendas e compras

def regras_vendas_compras(hoje):
    from djangosige.apps.vendas.models import OrcamentoVenda, PedidoVenda
    from djangosige.apps.compras.models import OrcamentoCompra, PedidoCompra

    alertas = []
    itens = [
        (PedidoVenda.objects.filter(data_entrega__lt=hoje, status='0'), ATENCAO, 'Vendas',
         ('pedido de venda com entrega atrasada', 'pedidos de venda com entrega atrasada'),
         'Cliente esperando: confira a entrega.', 'vendas:listapedidovendaatrasadosview'),
        (OrcamentoVenda.objects.filter(data_vencimento__lt=hoje, status='0'), ATENCAO, 'Vendas',
         ('orçamento de venda vencido', 'orçamentos de venda vencidos'),
         'Retome o contato antes de perder a venda.', 'vendas:listaorcamentovendavencidoview'),
        (PedidoCompra.objects.filter(data_entrega__lt=hoje, status='0'), ATENCAO, 'Compras',
         ('pedido de compra atrasado', 'pedidos de compra atrasados'),
         'O fornecedor ainda não entregou.', 'compras:listapedidocompraatrasadosview'),
        (OrcamentoCompra.objects.filter(data_vencimento__lt=hoje, status='0'), INFO, 'Compras',
         ('orçamento de compra vencido', 'orçamentos de compra vencidos'),
         'Preços podem ter mudado.', 'compras:listaorcamentocompravencidosview'),
    ]
    for qs, gravidade, modulo, nomes, detalhe, url_name in itens:
        n = qs.count()
        if n:
            alertas.append(Alerta(gravidade, modulo, plural(n, *nomes), detalhe, reverse(url_name)))
    return alertas


# ------------------------------------------------------------------ Estoque

def regras_estoque(hoje):
    from djangosige.apps.cadastro.models import Produto

    alertas = []
    baixo = Produto.objects.filter(estoque_minimo__gt=0, estoque_atual__lte=F('estoque_minimo'))
    zerados = baixo.filter(estoque_atual__lte=0).count()
    n = baixo.count()
    if zerados:
        alertas.append(Alerta(CRITICO, 'Estoque', f'{plural(zerados, "produto sem estoque", "produtos sem estoque")}',
                              'Sem saldo para vender. Programe a reposição.',
                              reverse('cadastro:listaprodutosbaixoestoqueview')))
    if n - zerados:
        alertas.append(Alerta(ATENCAO, 'Estoque', f'{plural(n - zerados, "produto abaixo do mínimo", "produtos abaixo do mínimo")}',
                              'Estoque igual ou menor que o mínimo cadastrado.',
                              reverse('cadastro:listaprodutosbaixoestoqueview')))
    return alertas


# ---------------------------------------------- Controle gerencial (fornecedores)

def regras_gerencial(hoje):
    from djangosige.apps.gerencial.models import PagamentoFornecedor

    alertas = []
    url = reverse('gerencial:dashboard')
    abertos = PagamentoFornecedor.objects.filter(status__in=['pendente', 'vencido'])

    r = abertos.filter(data_vencimento__lt=hoje).aggregate(n=Count('id'), total=Sum('valor'))
    if r['n']:
        alertas.append(Alerta(CRITICO, 'Gerencial', f'{plural(r["n"], "pagamento a fornecedor vencido", "pagamentos a fornecedores vencidos")}',
                              f'{moeda(r["total"])} em atraso com fornecedores.', url, r['total']))
    r = abertos.filter(data_vencimento__gte=hoje, data_vencimento__lte=hoje + timedelta(days=DIAS_PROXIMOS)).aggregate(
        n=Count('id'), total=Sum('valor'))
    if r['n']:
        alertas.append(Alerta(ATENCAO, 'Gerencial', f'{plural(r["n"], "pagamento a fornecedor", "pagamentos a fornecedores")} nos próximos {DIAS_PROXIMOS} dias',
                              f'Total de {moeda(r["total"])}.', url, r['total']))

    # Concentracao: um fornecedor com mais da metade da divida
    total = abertos.aggregate(t=Sum('valor'))['t'] or 0
    maior = abertos.values('fornecedor__nome_razao_social').annotate(t=Sum('valor')).order_by('-t').first()
    if maior and total and maior['t'] / total > Decimal('0.5') and abertos.values('fornecedor').distinct().count() > 1:
        pct = maior['t'] / total * 100
        alertas.append(Alerta(INFO, 'Gerencial', 'Dívida concentrada em um fornecedor',
                              f'{maior["fornecedor__nome_razao_social"]} responde por {pct:.0f}% do que está em aberto '
                              f'({moeda(maior["t"])}).', url, maior['t']))
    return alertas


# ------------------------------------------------------------------ Juridico

def regras_juridico(hoje):
    from djangosige.apps.juridico.models import Processo, Prazo

    alertas = []
    url = reverse('juridico:dashboard')
    limite = hoje + timedelta(days=DIAS_PROXIMOS)

    def gravidade_prazo(prazo):
        dias = (prazo - hoje).days
        if dias <= 3:
            return CRITICO
        return ATENCAO

    com_prazo_cadastrado = set()
    prazos = (Prazo.objects.filter(status='pendente', data_vencimento__lte=limite,
                                   processo__status='ativo')
              .select_related('processo').order_by('data_vencimento'))
    for p in prazos:
        com_prazo_cadastrado.add(p.processo_id)
        alertas.append(Alerta(gravidade_prazo(p.data_vencimento), 'Jurídico',
                              f'Prazo processual: {p.descricao}',
                              f'Processo {p.processo.numero} ({p.processo.parte_contraria}) — {quando(p.data_vencimento, hoje)}.',
                              reverse('juridico:processo_detail', args=[p.processo_id]), prazo=p.data_vencimento))

    processos = (Processo.objects.filter(status='ativo', proximo_prazo__isnull=False, proximo_prazo__lte=limite)
                 .exclude(pk__in=com_prazo_cadastrado).order_by('proximo_prazo'))
    for p in processos:
        alertas.append(Alerta(gravidade_prazo(p.proximo_prazo), 'Jurídico',
                              f'Prazo do processo {p.numero}',
                              f'{p.descricao_prazo or "Próximo prazo"} ({p.parte_contraria}) — {quando(p.proximo_prazo, hoje)}.',
                              reverse('juridico:processo_detail', args=[p.pk]), prazo=p.proximo_prazo))

    alto = Processo.objects.filter(status='ativo', nivel_risco='alto')
    n = alto.count()
    if n:
        em_risco = sum(Decimal(str(p.valor_risco)) for p in alto.only('valor_causa', 'probabilidade_perda'))
        sem_alerta = alto.filter(diretoria_alertada=False).count()
        detalhe = f'Valor estimado em risco: {moeda(em_risco)} (valor da causa × chance de perda).'
        if sem_alerta:
            detalhe += f' {plural(sem_alerta, "ainda não foi levado", "ainda não foram levados")} à diretoria.'
        alertas.append(Alerta(ATENCAO, 'Jurídico', f'{plural(n, "processo de risco alto", "processos de risco alto")}',
                              detalhe, url, em_risco))
    return alertas


# ---------------------------------------------------- Calendario financeiro

def regras_calendario(hoje):
    from djangosige.apps.financeiro.models import ItemCalendario

    url = reverse('financeiro:calendarioview')
    limite = hoje + timedelta(days=DIAS_PROXIMOS)
    # A planilha importada traz anos de historico: atraso so olha os ultimos 30 dias
    inicio = hoje - timedelta(days=30)
    pendentes = ItemCalendario.objects.filter(concluido=False)

    def resumo(filtro):
        r = pendentes.filter(filtro).aggregate(n=Count('id'), total=Sum('valor'))
        return r['n'], r['total'] or Decimal(0)

    alertas = []
    n, total = resumo(Q(data__gte=inicio, data__lt=hoje))
    if n:
        alertas.append(Alerta(CRITICO, 'Financeiro', f'{plural(n, "item atrasado", "itens atrasados")} no calendário',
                              f'{moeda(total)} em itens com data vencida nos últimos 30 dias.', url, total))
    n, total = resumo(Q(data=hoje))
    if n:
        alertas.append(Alerta(ATENCAO, 'Financeiro', f'{plural(n, "item para hoje", "itens para hoje")} no calendário',
                              f'Total de {moeda(total)}.', url, total, hoje))
    n, total = resumo(Q(data__gt=hoje, data__lte=limite))
    if n:
        alertas.append(Alerta(INFO, 'Financeiro', f'{plural(n, "item", "itens")} nos próximos {DIAS_PROXIMOS} dias no calendário',
                              f'Total de {moeda(total)}.', url, total))
    return alertas


# ---------------------------------------------------------------- Importacao

def regras_importacao(hoje):
    from djangosige.apps.importacao.models import ContainerImportacao, CustoImportacao, EtapaImportacao, ProcessoImportacao

    alertas = []
    limite = hoje + timedelta(days=DIAS_PROXIMOS)
    em_andamento = ProcessoImportacao.objects.filter(status='andamento')

    # Container ainda nao devolvido: free time acabando ou demurrage correndo
    containers = (ContainerImportacao.objects.filter(processo__in=em_andamento, data_devolucao__isnull=True)
                  .select_related('processo').prefetch_related('processo__etapas'))
    for container in containers:
        prazo = container.prazo_devolucao
        if not prazo or prazo > limite:
            continue
        url = container.processo.get_absolute_url()
        if prazo < hoje:
            alertas.append(Alerta(CRITICO, 'Importação', f'Demurrage: container {container.numero}',
                                  f'Processo {container.processo.referencia}: {container.dias_demurrage} dia(s) após o free time, '
                                  f'estimativa de {moeda(container.valor_demurrage)}.', url, container.valor_demurrage, prazo))
        else:
            gravidade = CRITICO if (prazo - hoje).days <= 3 else ATENCAO
            alertas.append(Alerta(gravidade, 'Importação', f'Devolver container {container.numero}',
                                  f'Processo {container.processo.referencia}: free time termina em {prazo:%d/%m/%Y}.', url, prazo=prazo))

    # Etapa atrasada: um alerta por processo, na primeira etapa pendente
    atrasadas = (EtapaImportacao.objects.filter(processo__in=em_andamento, nao_aplica=False, data_realizada__isnull=True,
                                                data_prevista__lt=hoje)
                 .select_related('processo').order_by('processo_id', 'ordem'))
    vistos = set()
    for etapa in atrasadas:
        if etapa.processo_id not in vistos:
            vistos.add(etapa.processo_id)
            alertas.append(Alerta(ATENCAO, 'Importação', f'Etapa atrasada: {etapa}',
                                  f'Processo {etapa.processo.referencia}: estava prevista para {etapa.data_prevista:%d/%m/%Y}.',
                                  etapa.processo.get_absolute_url(), prazo=etapa.data_prevista))

    chegadas = (EtapaImportacao.objects.filter(processo__in=em_andamento, codigo='chegada', data_realizada__isnull=True,
                                               data_prevista__gte=hoje, data_prevista__lte=limite)
                .select_related('processo'))
    for etapa in chegadas:
        alertas.append(Alerta(INFO, 'Importação', f'Chegada prevista: {etapa.processo.referencia}',
                              f'{etapa.processo.mercadoria} prevista para {etapa.data_prevista:%d/%m/%Y}.',
                              etapa.processo.get_absolute_url(), prazo=etapa.data_prevista))

    custos = (CustoImportacao.objects.filter(processo__in=em_andamento, pago=False, data_vencimento__lte=limite)
              .select_related('processo'))
    for custo in custos:
        gravidade = CRITICO if custo.data_vencimento < hoje else ATENCAO
        alertas.append(Alerta(gravidade, 'Importação', f'Custo a pagar: {custo}',
                              f'Processo {custo.processo.referencia}: {moeda(custo.valor)}, {quando(custo.data_vencimento, hoje)}.',
                              custo.processo.get_absolute_url(), custo.valor, custo.data_vencimento))
    return alertas


# -------------------------------------------------------- Financeiro do grupo

def regras_grupo(hoje):
    from djangosige.apps.financeiro_grupo.models import TransferenciaGrupo

    alertas = []
    paradas = TransferenciaGrupo.objects.filter(status='pendente', data__date__lt=hoje - timedelta(days=3))
    r = paradas.aggregate(n=Count('id'), total=Sum('valor'))
    if r['n']:
        alertas.append(Alerta(ATENCAO, 'Grupo', f'{plural(r["n"], "transferência pendente", "transferências pendentes")} há mais de 3 dias',
                              f'{moeda(r["total"])} entre empresas do grupo sem confirmação.',
                              reverse('financeiro_grupo:dashboard'), r['total']))
    return alertas


# -------------------------------------------------------------- Contabilidade

def regras_contabilidade(hoje):
    from djangosige.apps.contabilidade.models import (
        ObrigacaoAcessoria, ApuracaoTributos, Fiscal, ProcessoContabil)

    alertas = []
    limite = hoje + timedelta(days=DIAS_PROXIMOS)

    obrigacoes = (ObrigacaoAcessoria.objects.filter(entregue=False, data_vencimento__lte=limite)
                  .select_related('fiscal__processo__empresa', 'fiscal__processo__cliente').order_by('data_vencimento'))
    for o in obrigacoes:
        processo = o.fiscal.processo
        gravidade = CRITICO if o.data_vencimento <= hoje + timedelta(days=2) else ATENCAO
        alertas.append(Alerta(gravidade, 'Contabilidade',
                              f'{o.get_tipo_display()} {o.mes_referencia:02d}/{o.ano_referencia} não entregue',
                              f'{processo.nome_empresa} — {quando(o.data_vencimento, hoje)}. Atraso gera multa.',
                              _url_contabil(processo, 'fiscal'), prazo=o.data_vencimento))

    # Tributos apurados e nao pagos. O vencimento usado e o dia 20 do mes
    # seguinte a referencia (data usual de DAS, PIS/COFINS e ICMS).
    for a in ApuracaoTributos.objects.filter(pago=False, total_tributos__gt=0).select_related('fiscal__processo__empresa', 'fiscal__processo__cliente'):
        ano, mes = (a.ano_referencia + 1, 1) if a.mes_referencia == 12 else (a.ano_referencia, a.mes_referencia + 1)
        vencimento = date(ano, mes, 20)
        if vencimento > limite:
            continue
        processo = a.fiscal.processo
        alertas.append(Alerta(CRITICO if vencimento <= hoje else ATENCAO, 'Contabilidade',
                              f'Tributos de {a.mes_referencia:02d}/{a.ano_referencia} não pagos',
                              f'{processo.nome_empresa}: {moeda(a.total_tributos)} — {quando(vencimento, hoje)} (previsto dia 20).',
                              _url_contabil(processo, 'fiscal'), a.total_tributos, vencimento))

    n = Fiscal.objects.filter(em_dia=False, processo__ativo=True).count()
    if n:
        alertas.append(Alerta(ATENCAO, 'Contabilidade', f'{plural(n, "empresa com fiscal em atraso", "empresas com fiscal em atraso")}',
                              'Marcadas como "fora do dia" nos dados fiscais.', reverse('contabilidade:dashboard')))
    return alertas


def _url_contabil(processo, area):
    if processo.empresa_id:
        return reverse('contabilidade:empresa', args=[processo.empresa_id]) + '#' + area
    return reverse('contabilidade:dashboard')


REGRAS = [
    regras_financeiro,
    regras_calendario,
    regras_importacao,
    regras_vendas_compras,
    regras_estoque,
    regras_gerencial,
    regras_juridico,
    regras_grupo,
    regras_contabilidade,
]


def analisar(hoje=None):
    """Roda todas as regras e devolve os alertas, do mais grave ao menos grave."""
    hoje = hoje or date.today()
    alertas = []
    for regra in REGRAS:
        try:
            alertas.extend(regra(hoje))
        except Exception:
            logger.exception('Agente administrativo: falha na regra %s', regra.__name__)
    alertas.sort(key=lambda a: (ORDEM_GRAVIDADE[a.gravidade],
                                a.prazo or date.max,
                                -(a.valor or 0)))
    return alertas


def alertas_em_cache():
    """Mesma analise, guardada por alguns minutos para nao pesar em cada pagina."""
    dados = cache.get(CACHE_KEY)
    if dados is None:
        dados = [asdict(a) for a in analisar()]
        cache.set(CACHE_KEY, dados, CACHE_SEGUNDOS)
    return [Alerta(**d) for d in dados]


def limpar_cache():
    cache.delete(CACHE_KEY)


def contar(alertas):
    resumo = {CRITICO: 0, ATENCAO: 0, INFO: 0}
    for a in alertas:
        resumo[a.gravidade] += 1
    return resumo
