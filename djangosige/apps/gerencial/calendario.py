# -*- coding: utf-8 -*-
"""Calendário do Controle gerencial: vencimentos da planilha de negociações e
os pagamentos registrados no sistema (com comprovante), dia a dia."""
import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

NOMES_MESES = ('', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto',
               'Setembro', 'Outubro', 'Novembro', 'Dezembro')
DIAS_SEMANA = ('Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado')
ITENS_VISIVEIS = 3


def _dec(valor):
    try:
        return Decimal(str(valor if valor not in (None, '') else 0))
    except (InvalidOperation, ValueError):
        return Decimal('0')


def mes_pedido(request, hoje):
    try:
        ano = int(request.GET.get('cal_ano') or hoje.year)
        mes = int(request.GET.get('cal_mes') or hoje.month)
        date(ano, mes, 1)
    except ValueError:
        ano, mes = hoje.year, hoje.month
    return ano, mes


def vencimento(record, hoje):
    """Um item da planilha no calendário: valor da parcela e situação."""
    if 'payment_value' in record:
        return {'status': 'pago', 'valor': _dec(record.get('payment_value')), 'parcelas': ''}
    total_parcelas = int(_dec(record.get('installment_count')))
    pagas = min(int(_dec(record.get('paid_installments'))), total_parcelas) if total_parcelas else 0
    valor = _dec(record.get('installment_value')) or _dec(record.get('total_value'))
    if total_parcelas and pagas >= total_parcelas:
        status = 'pago'
    elif record['due_date'] < hoje:
        status = 'vencido'
    else:
        status = 'futuro'
    return {'status': status, 'valor': valor,
            'parcelas': '%d de %d pagas' % (pagas, total_parcelas) if total_parcelas > 1 else ''}


def montar(records, pagamentos, ano, mes, hoje):
    semanas_mes = calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes)
    inicio, fim = semanas_mes[0][0], semanas_mes[-1][-1]
    itens = defaultdict(list)
    for record in records:
        dia = record.get('due_date')
        if not dia or not (inicio <= dia <= fim):
            continue
        item = vencimento(record, hoje)
        item.update({'fornecedor': record.get('supplier') or '', 'pedido': record.get('order_number') or '',
                     'produto': record.get('product') or ''})
        itens[dia].append(item)
    pagos = defaultdict(list)
    for pagamento in pagamentos:
        if inicio <= pagamento.data <= fim:
            pagos[pagamento.data].append(pagamento)

    ordem = {'vencido': 0, 'futuro': 1, 'pago': 2}
    resumo = {'a_vencer': Decimal('0'), 'vencido': Decimal('0'), 'pago_planilha': Decimal('0'),
              'pago_registrado': Decimal('0'), 'pagamentos': 0}
    semanas = []
    for semana in semanas_mes:
        dias = []
        for dia in semana:
            lista = sorted(itens.get(dia, []), key=lambda i: (ordem[i['status']], i['fornecedor'], i['pedido']))
            no_mes = dia.month == mes
            if no_mes:
                for i in lista:
                    chave = {'vencido': 'vencido', 'futuro': 'a_vencer', 'pago': 'pago_planilha'}[i['status']]
                    resumo[chave] += i['valor']
                for p in pagos.get(dia, []):
                    resumo['pago_registrado'] += p.valor
                    resumo['pagamentos'] += 1
            dias.append({
                'data': dia, 'no_mes': no_mes, 'hoje': dia == hoje,
                'itens': lista[:ITENS_VISIVEIS], 'mais': lista[ITENS_VISIVEIS:],
                'pagamentos': pagos.get(dia, []),
                'a_pagar': sum((i['valor'] for i in lista if i['status'] != 'pago'), Decimal('0')),
            })
        semanas.append(dias)

    anterior = date(ano - 1, 12, 1) if mes == 1 else date(ano, mes - 1, 1)
    proximo = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return {'semanas': semanas, 'dias_semana': DIAS_SEMANA, 'nome_mes': NOMES_MESES[mes], 'ano': ano,
            'mes': mes, 'anterior': anterior, 'proximo': proximo, 'resumo': resumo,
            'inicio_mes': date(ano, mes, 1), 'fim_mes': _fim_mes(ano, mes)}


def _fim_mes(ano, mes):
    return date(ano, mes, calendar.monthrange(ano, mes)[1])
