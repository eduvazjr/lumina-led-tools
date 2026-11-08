"""Componentes visuais do Led Gerencial.

Uso nos templates: {% load led_ui %}

    {% valor_brl total %}            R$ pequeno, inteiro grande, centavos menores
    {% valor_brl total "sm" %}       mesma estrutura em tamanho de tabela
    {{ valor|brl }}                  texto simples: R$ 1.234,56
    {% secao_menu %}                 grupo do menu da página atual (breadcrumb)
"""
from django import template
from django.utils.html import format_html

from djangosige.apps.gerencial.templatetags.gerencial_format import _as_decimal, ptbr_number

register = template.Library()


@register.filter
def brl(value):
    """R$ 1.234,56 (negativos como -R$ 1.234,56)."""
    number = _as_decimal(value)
    texto = ptbr_number(abs(number), 2)
    return ('-R$ %s' if number < 0 else 'R$ %s') % texto


@register.simple_tag
def valor_brl(value, tamanho=''):
    number = _as_decimal(value)
    inteiro, centavos = ptbr_number(abs(number), 2).rsplit(',', 1)
    sinal = '-' if number < 0 else ''
    classe = 'valor valor-%s' % tamanho if tamanho else 'valor'
    return format_html(
        '<span class="{}"><span class="valor-moeda">{}R$</span>'
        '<span class="valor-inteiro">{}</span><span class="valor-centavos">,{}</span></span>',
        classe, sinal, inteiro, centavos,
    )


# Rótulo do grupo do menu lateral para cada app (namespace da URL).
SECOES = {
    'vendas': 'Vendas', 'compras': 'Compras', 'estoque': 'Estoque',
    'financeiro': 'Finanças', 'fiscal': 'Fiscal', 'cadastro': 'Cadastros',
    'importacao': 'Importações', 'gerencial': 'Gestão', 'financeiro_grupo': 'Gestão',
    'juridico': 'Gestão', 'contabilidade': 'Gestão', 'login': 'Administração',
}
RH_URLS = ('funcionario', 'folha', 'rh_')


@register.simple_tag(takes_context=True)
def secao_menu(context):
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if not match:
        return ''
    if match.namespace == 'contabilidade' and any(p in (match.url_name or '') for p in RH_URLS):
        return 'RH / Dep. Pessoal'
    if match.url_name == 'importacaoview':
        return 'Importações'
    if match.url_name == 'perfilview':
        return 'Minha conta'
    return SECOES.get(match.namespace, 'Visão geral')
