# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AnexosForm
from .models import Anexo
from .permissoes import pode_editar, pode_ver

ABRIR_NO_NAVEGADOR = ('pdf', 'jpg', 'jpeg', 'png')


def _avisar(request, tipo, texto):
    """Mostrado no próprio bloco Documentos ao voltar para a tela (as telas de cadastro
    não exibem as mensagens do Django)."""
    request.session['anexos_aviso'] = {'tipo': tipo, 'texto': texto}


def _voltar(request):
    destino = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        destino = '/'
    return redirect(destino.split('#')[0] + '#documentos')


@login_required
@require_POST
def enviar(request, content_type_id, object_id):
    content_type = get_object_or_404(ContentType, pk=content_type_id)
    modelo = content_type.model_class()
    if modelo is None or not modelo.objects.filter(pk=object_id).exists():
        raise Http404('Registro não encontrado.')
    if not pode_editar(request.user, content_type):
        raise PermissionDenied
    form = AnexosForm(request.POST, request.FILES)
    if form.is_valid():
        for arquivo in form.cleaned_data['arquivos']:
            Anexo.objects.create(
                content_type=content_type, object_id=object_id, arquivo=arquivo,
                nome=arquivo.name[:255], tamanho=arquivo.size, enviado_por=request.user)
        total = len(form.cleaned_data['arquivos'])
        _avisar(request, 'sucesso', '%d documento%s anexado%s.' % (total, 's' if total > 1 else '', 's' if total > 1 else ''))
    else:
        erros = [str(erro) for lista in form.errors.values() for erro in lista]
        _avisar(request, 'erro', ' '.join(erros))
    return _voltar(request)


@login_required
def baixar(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    if not pode_ver(request.user, anexo.content_type):
        raise PermissionDenied
    return FileResponse(anexo.arquivo.open('rb'), filename=anexo.nome,
                        as_attachment=anexo.extensao not in ABRIR_NO_NAVEGADOR)


@login_required
@require_POST
def remover(request, pk):
    anexo = get_object_or_404(Anexo, pk=pk)
    if not pode_editar(request.user, anexo.content_type):
        raise PermissionDenied
    nome = anexo.nome
    anexo.delete()
    _avisar(request, 'sucesso', 'Documento %s removido.' % nome)
    return _voltar(request)
