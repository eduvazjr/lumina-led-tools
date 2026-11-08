"""Componentes visuais do Led Gerencial.

Uso nos templates: {% load led_ui %}

    {% valor_brl total %}            R$ pequeno, inteiro grande, centavos menores
    {% valor_brl total "sm" %}       mesma estrutura em tamanho de tabela
    {{ valor|brl }}                  texto simples: R$ 1.234,56
    {% secao_menu %}                 grupo do menu da página atual (breadcrumb)
"""
from decimal import Decimal, InvalidOperation

from django import template
from django.utils.html import format_html

from djangosige.apps.gerencial.templatetags.gerencial_format import ptbr_number

register = template.Library()


def _as_decimal(value):
    """Aceita número, '1234.56', '1,234.56' (formato americano) ou '1.234,56'."""
    if value in (None, ''):
        return Decimal('0')
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    texto = str(value).replace('R$', '').replace(' ', '').replace('\xa0', '').strip()
    if ',' in texto and '.' in texto:
        if texto.rfind('.') > texto.rfind(','):
            texto = texto.replace(',', '')
        else:
            texto = texto.replace('.', '').replace(',', '.')
    elif ',' in texto:
        texto = texto.replace(',', '.')
    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError):
        return Decimal('0')


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


# Rótulos que vêm dos models sem acento (verbose_name automático)
ACENTOS = {
    'numero': 'número', 'operacao': 'operação', 'juridica': 'jurídica', 'emissao': 'emissão',
    'inscricao': 'inscrição', 'alvara': 'alvará', 'licencas': 'licenças', 'orgaos': 'órgãos',
    'conclusao': 'conclusão', 'observacoes': 'observações', 'observacao': 'observação',
    'descricao': 'descrição', 'situacao': 'situação', 'regime': 'regime', 'tributario': 'tributário',
    'referencia': 'referência', 'mes': 'mês', 'servico': 'serviço', 'informacoes': 'informações',
    'responsavel': 'responsável', 'periodo': 'período', 'salario': 'salário', 'admissao': 'admissão',
    'demissao': 'demissão', 'funcao': 'função', 'endereco': 'endereço', 'razao': 'razão',
    'contabil': 'contábil', 'contabeis': 'contábeis', 'balanco': 'balanço', 'apuracao': 'apuração',
    'conciliacao': 'conciliação', 'demonstracao': 'demonstração', 'liquido': 'líquido', 'liquida': 'líquida',
    'necessaria': 'necessária', 'necessarias': 'necessárias', 'proximo': 'próximo', 'ultima': 'última',
    'ultimo': 'último', 'distribuicao': 'distribuição', 'orgao': 'órgão', 'nivel': 'nível',
    'cnpj': 'CNPJ', 'cpf': 'CPF', 'rg': 'RG', 'ie': 'IE', 'nire': 'NIRE', 'icms': 'ICMS', 'iss': 'ISS',
    'pis': 'PIS', 'cofins': 'COFINS', 'irpj': 'IRPJ', 'csll': 'CSLL', 'inss': 'INSS', 'fgts': 'FGTS',
    'dre': 'DRE', 'sped': 'SPED', 'nf': 'NF', 'nfe': 'NF-e', 'cfop': 'CFOP', 'ncm': 'NCM',
}


@register.filter
def rotulo_pt(texto):
    """'Numero protocolo junta' -> 'Número protocolo junta'; 'Cnpj' -> 'CNPJ'."""
    palavras = str(texto or '').split(' ')
    saida = []
    for i, palavra in enumerate(palavras):
        troca = ACENTOS.get(palavra.lower())
        if troca:
            if i == 0 and troca.islower():
                troca = troca[0].upper() + troca[1:]
            palavra = troca
        saida.append(palavra)
    return ' '.join(saida)


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
