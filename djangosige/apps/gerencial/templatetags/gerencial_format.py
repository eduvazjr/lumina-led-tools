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
