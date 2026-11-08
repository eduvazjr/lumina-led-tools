# -*- coding: utf-8 -*-
"""Exportação de qualquer tabela do sistema para CSV ou PDF.

O navegador envia o conteúdo da tabela que está na tela (cabeçalhos e linhas
já filtradas) e o servidor devolve o arquivo. O PDF é montado só com esse
texto, escapado pelo template; o WeasyPrint não busca nada externo.
"""
import csv
import io
import json
import re
import unicodedata

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .pdf import carregar_weasyprint

MAX_LINHAS = 20000
MAX_COLUNAS = 40
MAX_CELULA = 2000
MAX_BYTES = 15 * 1024 * 1024
VALOR_BR = re.compile(r'^-?\s*(?:-?R\$\s*)?-?\d{1,3}(?:\.\d{3})*(?:,\d+)?%?$')


def _texto(valor, limite=MAX_CELULA):
    return ' '.join(str(valor if valor is not None else '').split())[:limite]


def _nome_arquivo(titulo, extensao):
    base = unicodedata.normalize('NFKD', titulo).encode('ascii', 'ignore').decode().lower()
    base = re.sub(r'[^a-z0-9]+', '-', base).strip('-') or 'exportacao'
    return '%s-%s.%s' % (base[:60], timezone.localdate().strftime('%Y-%m-%d'), extensao)


def _ler_dados(request):
    arquivo = request.FILES.get('dados')
    bruto = arquivo.read(MAX_BYTES + 1) if arquivo else request.POST.get('dados', '').encode()
    if len(bruto) > MAX_BYTES:
        raise ValueError('Tabela grande demais para exportar.')
    dados = json.loads(bruto.decode('utf-8'))
    colunas = [_texto(c, 200) for c in dados.get('colunas', [])][:MAX_COLUNAS]
    if not colunas:
        raise ValueError('Tabela sem colunas.')
    alinhamentos = [a if a in ('esquerda', 'direita') else 'esquerda' for a in dados.get('alinhamentos', [])][:len(colunas)]
    alinhamentos += ['esquerda'] * (len(colunas) - len(alinhamentos))
    linhas = []
    for linha in dados.get('linhas', [])[:MAX_LINHAS]:
        celulas = [_texto(c) for c in list(linha)[:len(colunas)]]
        linhas.append(celulas + [''] * (len(colunas) - len(celulas)))
    rodape = [_texto(c) for c in list(dados.get('rodape') or [])[:len(colunas)]]
    return {
        'titulo': _texto(dados.get('titulo') or 'Exportação', 200),
        'subtitulo': _texto(dados.get('subtitulo') or '', 400),
        'colunas': colunas, 'alinhamentos': alinhamentos, 'linhas': linhas,
        'rodape': rodape + [''] * (len(colunas) - len(rodape)) if rodape else [],
    }


def _valor_para_planilha(celula):
    """'R$ 1.234,56' vira '1234,56' para o Excel em português somar a coluna."""
    if celula and VALOR_BR.match(celula) and not celula.endswith('%'):
        negativo = celula.lstrip().startswith('-')
        numero = celula.replace('R$', '').replace('-', '').replace('.', '').strip()
        return ('-' if negativo else '') + numero
    return celula


def gerar_csv(dados):
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    escritor.writerow(dados['colunas'])
    for linha in dados['linhas']:
        escritor.writerow([_valor_para_planilha(c) for c in linha])
    if dados['rodape']:
        escritor.writerow([_valor_para_planilha(c) for c in dados['rodape']])
    return '﻿' + saida.getvalue()  # BOM: o Excel reconhece os acentos


def _sem_acesso_externo(url, *args, **kwargs):
    raise ValueError('Recursos externos não são carregados no PDF.')


def gerar_pdf(dados, usuario):
    HTML = carregar_weasyprint()
    if HTML is None:
        return None
    classes = ['direita' if a == 'direita' else '' for a in dados['alinhamentos']]
    html = render_to_string('base/exportar_pdf.html', dict(
        dados, gerado_em=timezone.localtime(), usuario=usuario,
        paisagem=len(dados['colunas']) > 6, total_linhas=len(dados['linhas']),
        cabecalho=list(zip(dados['colunas'], classes)),
        linhas_pdf=[list(zip(linha, classes)) for linha in dados['linhas']],
        rodape_pdf=list(zip(dados['rodape'], classes)) if dados['rodape'] else []))
    return HTML(string=html, url_fetcher=_sem_acesso_externo).write_pdf()


@login_required
@require_POST
def exportar(request, formato):
    try:
        dados = _ler_dados(request)
    except (ValueError, TypeError, AttributeError, UnicodeDecodeError) as erro:
        return HttpResponseBadRequest(str(erro) or 'Dados inválidos.')
    if formato == 'csv':
        resposta = HttpResponse(gerar_csv(dados), content_type='text/csv; charset=utf-8')
        resposta['Content-Disposition'] = 'attachment; filename="%s"' % _nome_arquivo(dados['titulo'], 'csv')
        return resposta
    pdf = gerar_pdf(dados, request.user)
    if pdf is None:
        return HttpResponse('O gerador de PDF não está disponível neste servidor.', status=503, content_type='text/plain; charset=utf-8')
    resposta = HttpResponse(pdf, content_type='application/pdf')
    resposta['Content-Disposition'] = 'attachment; filename="%s"' % _nome_arquivo(dados['titulo'], 'pdf')
    return resposta
