# -*- coding: utf-8 -*-

from djangosige.apps.base import agente


def alertas_agente(request):
    # Contador do topo: usa o cache do agente para nao pesar em cada pagina
    if not request.user.is_authenticated:
        return {}
    try:
        resumo = agente.contar(agente.alertas_em_cache())
    except Exception:
        return {}
    return {
        'agente_criticos': resumo[agente.CRITICO],
        'agente_pendentes': resumo[agente.CRITICO] + resumo[agente.ATENCAO],
    }
