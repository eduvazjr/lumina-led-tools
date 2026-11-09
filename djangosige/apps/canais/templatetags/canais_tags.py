# -*- coding: utf-8 -*-
from decimal import Decimal

from django import template
from django.utils.html import format_html

from djangosige.apps.gerencial.templatetags.gerencial_format import ptbr_number
from djangosige.apps.base.templatetags.led_ui import brl

register = template.Library()


@register.simple_tag
def variacao(v, inverso=False, moeda=True):
    """Comparação com o período anterior: '+11% · +R$ 405.554,00'.
    inverso=True para custos, cancelamentos e devoluções (subir é ruim)."""
    if not v:
        return format_html('<span class="variacao">Sem comparação</span>')
    pct, dif = v['pct'], v['dif']
    if dif == 0:
        classe = ''
    else:
        bom = (dif > 0) != bool(inverso)
        classe = ' is-positivo' if bom else ' is-negativo'
    sinal = '+' if dif > 0 else ('-' if dif < 0 else '')
    dif_txt = brl(abs(dif)) if moeda else ptbr_number(abs(dif), 0)
    return format_html('<span class="variacao{}">{}{}% · {}{}</span>', classe, sinal,
                       ptbr_number(abs(pct), 1 if abs(pct) < 10 else 0), sinal, dif_txt)


@register.filter
def pct(valor):
    if valor is None:
        return '—'
    return '%s%%' % ptbr_number(Decimal(valor), 1)


@register.filter
def ptbr_int(valor):
    return ptbr_number(Decimal(valor or 0), 0)
