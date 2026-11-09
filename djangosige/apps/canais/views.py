# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import PLATAFORMAS, ContaCanal, ResumoDiarioCanal, SincronizacaoBase

CAMPOS = ('pedidos', 'unidades', 'vendas_brutas', 'frete_cliente', 'cancelados_qtd', 'cancelados_valor',
          'devolucoes_qtd', 'devolucoes_valor', 'comissao_informada', 'base_sem_comissao', 'frete_vendedor',
          'custo', 'pedidos_sem_custo')
PERIODOS = [('7', 'Últimos 7 dias'), ('30', 'Últimos 30 dias'), ('mes', 'Este mês'),
            ('mes_anterior', 'Mês passado'), ('personalizado', 'Escolher datas')]
ZERO = Decimal('0.00')


def _periodo(request, hoje):
    escolha = request.GET.get('periodo') or '7'
    ontem = hoje - timedelta(days=1)
    if escolha == '30':
        inicio, fim = hoje - timedelta(days=30), ontem
    elif escolha == 'mes':
        inicio, fim = hoje.replace(day=1), hoje
    elif escolha == 'mes_anterior':
        fim = hoje.replace(day=1) - timedelta(days=1)
        inicio = fim.replace(day=1)
    elif escolha == 'personalizado':
        try:
            inicio = datetime.strptime(request.GET.get('de', ''), '%Y-%m-%d').date()
            fim = datetime.strptime(request.GET.get('ate', ''), '%Y-%m-%d').date()
        except ValueError:
            escolha, inicio, fim = '7', hoje - timedelta(days=7), ontem
        if fim < inicio:
            inicio, fim = fim, inicio
    else:
        escolha, inicio, fim = '7', hoje - timedelta(days=7), ontem
    dias = (fim - inicio).days + 1
    if escolha == 'mes_anterior':
        fim_comp = inicio - timedelta(days=1)
        inicio_comp = fim_comp.replace(day=1)
    else:
        fim_comp = inicio - timedelta(days=1)
        inicio_comp = fim_comp - timedelta(days=dias - 1)
    return escolha, inicio, fim, inicio_comp, fim_comp


def metricas(soma, percentuais=None):
    """Indicadores a partir das somas do resumo diário. percentuais: comissão
    estimada por conta, aplicada sobre as vendas sem comissão informada."""
    s = {c: soma.get(c) or 0 for c in CAMPOS}
    for c in ('pedidos', 'unidades', 'cancelados_qtd', 'devolucoes_qtd', 'pedidos_sem_custo'):
        s[c] = int(s[c])
    estimada = soma.get('comissao_estimada', ZERO)
    canc_dev = s['cancelados_valor'] + s['devolucoes_valor']
    liquidas = s['vendas_brutas'] - canc_dev
    comissao = s['comissao_informada'] + estimada
    margem = liquidas - s['custo'] - comissao - s['frete_vendedor']
    return {
        'vendas_brutas': s['vendas_brutas'], 'cancelados_devolvidos': canc_dev, 'vendas_liquidas': liquidas,
        'pedidos': s['pedidos'], 'unidades': s['unidades'], 'cancelados_qtd': s['cancelados_qtd'],
        'custo': s['custo'], 'comissao': comissao, 'comissao_estimada': estimada,
        'frete_vendedor': s['frete_vendedor'], 'margem': margem, 'devolucoes_qtd': s['devolucoes_qtd'],
        'margem_pct': (margem / liquidas * 100) if liquidas else None,
        'ticket_medio': (s['vendas_brutas'] / s['pedidos']) if s['pedidos'] else None,
        'pedidos_sem_custo': s['pedidos_sem_custo'],
        'base_sem_comissao_sem_taxa': soma.get('base_sem_taxa', ZERO),
    }


def _somar(qs, contas):
    """Somas por conta e no total, já com a comissão estimada."""
    por_conta = {}
    for linha in qs.values('conta_id').annotate(**{c: Sum(c) for c in CAMPOS}):
        conta = contas.get(linha['conta_id'])
        pct = conta.comissao_percentual if conta else None
        linha['comissao_estimada'] = ((linha['base_sem_comissao'] or ZERO) * pct / 100).quantize(Decimal('0.01')) if pct else ZERO
        linha['base_sem_taxa'] = ZERO if pct else (linha['base_sem_comissao'] or ZERO)
        por_conta[linha['conta_id']] = linha
    total = defaultdict(lambda: ZERO)
    for linha in por_conta.values():
        for chave in CAMPOS + ('comissao_estimada', 'base_sem_taxa'):
            total[chave] += linha.get(chave) or 0
    return por_conta, total


def _variacao(atual, anterior):
    if anterior in (None, 0) or atual is None:
        return None
    return {'pct': (Decimal(atual) - Decimal(anterior)) / abs(Decimal(anterior)) * 100,
            'dif': Decimal(atual) - Decimal(anterior)}


@login_required
def painel(request):
    hoje = timezone.localdate()
    escolha, inicio, fim, inicio_comp, fim_comp = _periodo(request, hoje)
    contas = {c.pk: c for c in ContaCanal.objects.all()}
    plataforma = request.GET.get('plataforma') or ''
    base = ResumoDiarioCanal.objects.all()
    if plataforma:
        base = base.filter(conta__origem=plataforma)
    por_conta, total = _somar(base.filter(data__range=(inicio, fim)), contas)
    _, total_comp = _somar(base.filter(data__range=(inicio_comp, fim_comp)), contas)
    atual, anterior = metricas(total), metricas(total_comp)
    variacoes = {chave: _variacao(atual[chave], anterior[chave]) for chave in atual
                 if not isinstance(atual[chave], bool)}

    linhas_conta = sorted(({'conta': contas.get(pk), **metricas(soma)} for pk, soma in por_conta.items()),
                          key=lambda l: l['vendas_brutas'], reverse=True)
    dias = defaultdict(lambda: defaultdict(lambda: ZERO))
    for linha in base.filter(data__range=(inicio, fim)).values('data', 'conta_id').annotate(
            **{c: Sum(c) for c in CAMPOS}):
        conta = contas.get(linha['conta_id'])
        pct = conta.comissao_percentual if conta else None
        soma = dias[linha['data']]
        for c in CAMPOS:
            soma[c] += linha[c] or 0
        if pct:
            soma['comissao_estimada'] += ((linha['base_sem_comissao'] or ZERO) * pct / 100).quantize(Decimal('0.01'))
    por_dia = [{'data': data, **metricas(dias[data])} for data in sorted(dias, reverse=True)]

    ultima = SincronizacaoBase.objects.first()
    ultima_ok = SincronizacaoBase.objects.filter(completa=True).first()
    return render(request, 'canais/painel.html', {
        'atual': atual, 'anterior': anterior, 'v': variacoes, 'linhas_conta': linhas_conta, 'por_dia': por_dia,
        'inicio': inicio, 'fim': fim, 'inicio_comp': inicio_comp, 'fim_comp': fim_comp,
        'periodos': PERIODOS, 'periodo': escolha, 'plataforma': plataforma,
        'plataformas': sorted({(c.origem, c.plataforma) for c in contas.values()}, key=lambda p: p[1]),
        'ultima': ultima, 'ultima_ok': ultima_ok, 'tem_token': bool(getattr(settings, 'BASELINKER_TOKEN', '')),
        'tem_dados': ResumoDiarioCanal.objects.exists(),
        'sem_taxa': [c for c in contas.values() if c.comissao_percentual is None and c.origem != 'melibr'],
    })


@login_required
@require_POST
def sincronizar_agora(request):
    from .baselinker import sincronizar
    registro = sincronizar(limite_chamadas=40)
    if registro.completa:
        messages.success(request, 'Sincronizado: %d pedidos e %d devoluções lidos.' % (registro.pedidos, registro.devolucoes))
    elif registro.pedidos:
        messages.success(request, '%d pedidos lidos. %s' % (registro.pedidos, registro.erro))
    else:
        messages.error(request, registro.erro or 'Não foi possível sincronizar.')
    return redirect('canais:painel')


@login_required
def contas(request):
    lista = list(ContaCanal.objects.all())
    erros = {}
    if request.method == 'POST':
        for conta in lista:
            texto = (request.POST.get('pct_%s' % conta.pk) or '').strip().replace('%', '').replace(',', '.')
            if not texto:
                conta.comissao_percentual = None
            else:
                try:
                    valor = Decimal(texto)
                    if not (0 <= valor <= 100):
                        raise ValueError
                    conta.comissao_percentual = valor
                except Exception:
                    erros[conta.pk] = 'Use um número entre 0 e 100.'
                    continue
        if not erros:
            for conta in lista:
                conta.save(update_fields=['comissao_percentual'])
            messages.success(request, 'Comissões salvas.')
            return redirect('canais:painel')
    for conta in lista:
        conta.erro = erros.get(conta.pk)
    return render(request, 'canais/contas.html', {'contas': lista, 'plataformas': PLATAFORMAS})
