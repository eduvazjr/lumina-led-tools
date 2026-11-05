# -*- coding: utf-8 -*-

from .models import Usuario
from djangosige.apps.cadastro.models import MinhaEmpresa

# Manter foto do perfil na sidebar


def foto_usuario(request):
    context_dict = {}
    if not request.user.is_authenticated:
        return context_dict

    # Foto do usuario
    try:
        user_foto = Usuario.objects.only('user_foto').get(
            user=request.user).user_foto
        context_dict['user_foto_sidebar'] = user_foto
    except:
        pass

    # Empresa do usuario (uma consulta so, ja trazendo a empresa)
    try:
        user_empresa = MinhaEmpresa.objects.select_related('m_empresa').get(
            m_usuario__user=request.user).m_empresa
        if user_empresa:
            context_dict['user_empresa'] = user_empresa
    except:
        pass

    return context_dict
