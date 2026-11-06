# -*- coding: utf-8 -*-
"""Importa a planilha mensal "Contas a pagar" para o calendario financeiro.

Cada aba e um mes: uma grade de domingo a sabado em que cada celula traz o dia e,
nas linhas seguintes, os itens. Um item conta como concluido quando tem "OK" no
texto ou quando a celula de um dia util esta cinza (o dia foi fechado).
"""

import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction

from djangosige.apps.financeiro.models import ItemCalendario, ProgramacaoMes

MESES = {
    'JANEIRO': 1, 'FEVEREIRO': 2, 'MARCO': 3, 'MARÇO': 3, 'ABRIL': 4, 'MAIO': 5, 'JUNHO': 6,
    'JULHO': 7, 'AGOSTO': 8, 'SETEMBRO': 9, 'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12,
}
CINZA_DIA_FECHADO = 'FFB7B7B7'
VERMELHO = 'FFFF0000'
LINHAS_DA_GRADE = 6

RE_OK = re.compile(r'\bok\b\.?', re.I)
RE_VALOR = re.compile(r'R\$\s*(\d[\d.,]*)')
RE_RS_VAZIO = re.compile(r'R\$')
RE_DIA = re.compile(r'^\s*(\d{1,2})(?!\d)\s*-?\s*(.*)$', re.S)


def converter_valor(texto):
    texto = texto.rstrip('.,')
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    elif texto.count('.') >= 1 and len(texto.rsplit('.', 1)[-1]) == 3:
        texto = texto.replace('.', '')
    try:
        return Decimal(texto).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None


def separar_itens(linhas):
    """Recebe [(texto, vermelho)] e junta as continuacoes ao item anterior."""
    itens = []
    for texto, vermelho in linhas:
        limpo = texto.strip()
        if not limpo:
            continue
        if limpo.startswith('-') or not itens:
            itens.append([limpo.lstrip('- ').strip(), vermelho])
        else:
            itens[-1][0] += ' ' + limpo
            itens[-1][1] = itens[-1][1] or vermelho
    return [item for item in itens if item[0]]


def interpretar_item(texto):
    """Devolve (descricao, [valores], concluido). Varios valores viram varios itens."""
    concluido = bool(RE_OK.search(texto))
    valores = [converter_valor(v) for v in RE_VALOR.findall(texto)]
    descricao = RE_VALOR.sub(' ', RE_OK.sub(' ', texto))
    descricao = RE_RS_VAZIO.sub(' ', descricao)
    descricao = re.sub(r'\s*/\s*(?=/|$)', ' ', descricao)
    descricao = ' '.join(descricao.split()).strip(' -/')
    return descricao[:255], valores or [None], concluido


def _vermelho(cor):
    return cor is not None and cor.type == 'rgb' and cor.rgb == VERMELHO


def linhas_da_celula(celula):
    """Quebra a celula em linhas, indicando quais tem texto em vermelho."""
    cor_celula = celula.font.color if celula.font else None
    valor = celula.value
    if isinstance(valor, list):
        trechos = [(parte, _vermelho(cor_celula)) if isinstance(parte, str)
                   else (parte.text, _vermelho(parte.font.color if parte.font else None) or _vermelho(cor_celula))
                   for parte in valor]
    else:
        trechos = [(str(valor), _vermelho(cor_celula))]

    linhas = [['', False]]
    for texto, vermelho in trechos:
        for indice, pedaco in enumerate(texto.split('\n')):
            if indice:
                linhas.append(['', False])
            linhas[-1][0] += pedaco
            if pedaco.strip():
                linhas[-1][1] = linhas[-1][1] or vermelho
    return [tuple(linha) for linha in linhas]


def identificar_mes(aba):
    textos = [str(aba['C1'].value or ''), aba.title]
    for texto in textos:
        texto = texto.upper()
        for nome, mes in MESES.items():
            ano = re.search(r'%s\D*(20\d\d)' % nome, texto)
            if ano:
                return int(ano.group(1)), mes
    return None


def localizar_cabecalho(aba):
    for linha in aba.iter_rows(min_row=1, max_row=6):
        for celula in linha:
            if isinstance(celula.value, (str, list)) and 'DOMINGO' in str(celula.value).upper():
                return celula.row, celula.column
    return 2, 2


def data_da_celula(inicio_grade, linha, coluna, dia, mes):
    data = inicio_grade + timedelta(days=7 * linha + coluna)
    if dia is None or data.day == dia:
        return data
    # Numero do dia diferente da posicao (ha abas sem a primeira semana):
    # procura o dia na mesma coluna, dando preferencia ao mes da aba
    candidatas = [inicio_grade + timedelta(days=7 * semana + coluna) for semana in range(-1, LINHAS_DA_GRADE + 1)]
    candidatas = [candidata for candidata in candidatas if candidata.day == dia]
    candidatas.sort(key=lambda candidata: candidata.month != mes)
    return candidatas[0] if candidatas else data


def ler_aba(aba):
    """Devolve (competencia, {(data, descricao, valor): [quantidade, concluidos, destaque]}, programacao)."""
    identificado = identificar_mes(aba)
    if not identificado:
        return None
    ano, mes = identificado
    linha_cabecalho, coluna_domingo = localizar_cabecalho(aba)
    primeiro = date(ano, mes, 1)
    inicio_grade = primeiro - timedelta(days=(primeiro.weekday() + 1) % 7)

    itens = defaultdict(lambda: [0, 0, False])
    for linha in range(LINHAS_DA_GRADE):
        for coluna in range(7):
            celula = aba.cell(row=linha_cabecalho + 1 + linha, column=coluna_domingo + coluna)
            if celula.value is None or isinstance(celula.value, (int, float)):
                continue
            linhas = linhas_da_celula(celula)
            encontrado = RE_DIA.match(linhas[0][0])
            dia = None
            if encontrado:
                dia = int(encontrado.group(1))
                linhas[0] = (encontrado.group(2), linhas[0][1])
            data = data_da_celula(inicio_grade, linha, coluna, dia, mes)

            cor = celula.fill.fgColor.rgb if celula.fill and celula.fill.fill_type else None
            fechado = cor == CINZA_DIA_FECHADO and 0 < coluna < 6

            for texto, vermelho in separar_itens(linhas):
                descricao, valores, ok = interpretar_item(texto)
                if len(descricao) < 2:
                    continue
                for valor in valores:
                    registro = itens[(data, descricao, valor)]
                    registro[0] += 1
                    registro[1] += 1 if (ok or fechado) else 0
                    registro[2] = registro[2] or vermelho

    programacao = []
    for linha in aba.iter_rows(min_row=linha_cabecalho + 1, max_row=linha_cabecalho + LINHAS_DA_GRADE + 3,
                               min_col=coluna_domingo + 7, max_col=coluna_domingo + 7):
        for celula in linha:
            if isinstance(celula.value, (str, list)) and str(celula.value).strip():
                programacao.append(str(celula.value).strip())
    return (ano, mes), itens, '\n'.join(programacao)


def importar_planilha(arquivo):
    import openpyxl

    livro = openpyxl.load_workbook(arquivo, rich_text=True)
    combinados = {}
    programacoes = {}
    meses = set()
    abas_ignoradas = []

    for aba in livro.worksheets:
        resultado = ler_aba(aba)
        if not resultado:
            if aba.max_row > 1:
                abas_ignoradas.append(aba.title.strip())
            continue
        competencia, itens, programacao = resultado
        meses.add(competencia)
        if programacao:
            programacoes[competencia] = programacao
        # Um dia aparece em duas abas nas pontas da grade: vale a maior contagem
        for chave, (quantidade, concluidos, destaque) in itens.items():
            atual = combinados.get(chave, [0, 0, False])
            combinados[chave] = [max(atual[0], quantidade), max(atual[1], concluidos), atual[2] or destaque]

    resumo = Counter(meses=len(meses))
    with transaction.atomic():
        existentes = defaultdict(list)
        for item in ItemCalendario.objects.all():
            existentes[(item.data, item.descricao, item.valor)].append(item)

        novos = []
        for (data, descricao, valor), (quantidade, concluidos, destaque) in combinados.items():
            ja_salvos = existentes[(data, descricao, valor)]
            for indice in range(quantidade):
                concluido = indice < concluidos
                if indice < len(ja_salvos):
                    if concluido and not ja_salvos[indice].concluido:
                        ja_salvos[indice].concluido = True
                        ja_salvos[indice].save(update_fields=['concluido'])
                        resumo['atualizados'] += 1
                else:
                    novos.append(ItemCalendario(data=data, descricao=descricao, valor=valor,
                                                concluido=concluido, destaque=destaque))
        ItemCalendario.objects.bulk_create(novos, batch_size=500)
        resumo['criados'] = len(novos)
        resumo['concluidos'] = sum(1 for item in novos if item.concluido)
        resumo['sem_valor'] = sum(1 for item in novos if item.valor is None)

        for (ano, mes), texto in programacoes.items():
            programacao, _ = ProgramacaoMes.objects.get_or_create(ano=ano, mes=mes)
            if not programacao.texto.strip():
                programacao.texto = texto
                programacao.save()

    resumo['abas_ignoradas'] = len(abas_ignoradas)
    return resumo, abas_ignoradas
