# -*- coding: utf-8 -*-
"""{% load anexos %}{% documentos objeto %}: bloco 'Documentos' de qualquer registro."""
from django import template
from django.contrib.contenttypes.models import ContentType

from ..forms import AnexosForm
from ..models import Anexo
from ..permissoes import pode_editar, pode_ver

register = template.Library()


@register.inclusion_tag('anexos/bloco.html', takes_context=True)
def documentos(context, objeto, titulo='Documentos'):
    request = context.get('request')
    if objeto is None or not getattr(objeto, 'pk', None) or request is None:
        return {'mostrar': False}
    content_type = ContentType.objects.get_for_model(objeto.__class__)
    if not pode_ver(request.user, content_type):
        return {'mostrar': False}
    return {
        'mostrar': True,
        'titulo': titulo,
        'objeto': objeto,
        'content_type': content_type,
        'anexos': Anexo.objects.filter(content_type=content_type, object_id=objeto.pk).select_related('enviado_por'),
        'pode_editar': pode_editar(request.user, content_type),
        'aceita': AnexosForm.base_fields['arquivos'].widget.attrs.get('accept', ''),
        'voltar': request.get_full_path(),
        'csrf_token': context.get('csrf_token'),
        'aviso': request.session.pop('anexos_aviso', None) if hasattr(request, 'session') else None,
    }
