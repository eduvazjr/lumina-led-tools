# -*- coding: utf-8 -*-
"""Geracao de PDF com WeasyPrint.

A biblioteca e carregada so na hora de gerar o arquivo: no Windows ela
depende do GTK e, sem ele, o import falha. Assim o resto do sistema
continua funcionando e a tela de PDF mostra uma mensagem em vez de erro.
"""

import logging

logger = logging.getLogger(__name__)


def carregar_weasyprint():
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        logger.warning('WeasyPrint indisponivel; PDFs nao serao gerados.', exc_info=True)
        return None
    return HTML


def disponivel():
    return carregar_weasyprint() is not None


def html_para_pdf(html_string, base_url=None):
    """Devolve os bytes do PDF, ou None se o WeasyPrint nao estiver instalado."""
    HTML = carregar_weasyprint()
    if HTML is None:
        return None
    return HTML(string=html_string, base_url=base_url).write_pdf()
