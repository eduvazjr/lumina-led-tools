from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


def _as_decimal(value):
    if value in (None, ''):
        return Decimal('0')
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


@register.filter
def ptbr_number(value, decimal_places=2):
    try:
        places = max(0, int(decimal_places))
    except (TypeError, ValueError):
        places = 2
    number = _as_decimal(value)
    quantum = Decimal('1') if places == 0 else Decimal('1').scaleb(-places)
    number = number.quantize(quantum, rounding=ROUND_HALF_UP)
    formatted = format(number, f',.{places}f')
    return formatted.replace(',', '#').replace('.', ',').replace('#', '.')


@register.filter
def ptbr_currency(value):
    return 'R$ %s' % ptbr_number(value, 2)


@register.filter
def fornecedores_por_negociado(supplier_kpis):
    """Linhas da tabela por fornecedor, do maior valor negociado para o menor,
    com o percentual quitado (recebido / negociado)."""
    linhas = []
    for nome, dados in (supplier_kpis or {}).items():
        total = _as_decimal(dados.get('total_negotiated'))
        recebido = _as_decimal(dados.get('received_estimate'))
        pct = (recebido / total * 100) if total > 0 else None
        linhas.append({'nome': nome, 'dados': dados, 'pct': pct})
    return sorted(linhas, key=lambda linha: (-_as_decimal(linha['dados'].get('total_negotiated')), linha['nome']))


@register.filter
def com_vencidas(supplier_kpis):
    """Fornecedores que têm parcelas vencidas, do que tem mais para o que tem menos."""
    linhas = [(nome, dados) for nome, dados in (supplier_kpis or {}).items() if dados.get('overdue_installments')]
    return sorted(linhas, key=lambda item: -item[1]['overdue_installments'])


@register.filter
def com_pago_acima(supplier_kpis):
    """Fornecedores com pagamento acima do valor negociado."""
    return [(nome, dados) for nome, dados in (supplier_kpis or {}).items() if _as_decimal(dados.get('paid_above_negotiated')) > 0]


@register.filter
def quando_sincronizou(valor):
    """'2026-11-07T22:53:00-03:00' -> 'hoje às 22:53' / 'em 06/11/2026 às 22:53'."""
    from datetime import datetime
    from django.utils import timezone
    if not valor:
        return ''
    try:
        momento = valor if isinstance(valor, datetime) else datetime.fromisoformat(str(valor))
    except ValueError:
        return str(valor)
    if timezone.is_aware(momento):
        momento = timezone.localtime(momento)
    hoje = timezone.localdate()
    hora = momento.strftime('%H:%M')
    if momento.date() == hoje:
        return 'hoje às %s' % hora
    if (hoje - momento.date()).days == 1:
        return 'ontem às %s' % hora
    return 'em %s às %s' % (momento.strftime('%d/%m/%Y'), hora)


@register.filter
def percentual(parte, total):
    """parte / total * 100 (0 quando o total é zero)."""
    total = _as_decimal(total)
    return (_as_decimal(parte) / total * 100) if total else Decimal('0')
