# -*- coding: utf-8 -*-

from datetime import date

from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from djangosige.apps.base import agente
from djangosige.apps.base.custom_views import (
    CustomCreateView, CustomListView, CustomUpdateView, CustomView)

from .forms import (
    ContainerFormSet, CustoFormSet, DocumentosForm, EtapaFormSet, ProcessoImportacaoForm)
from .models import DocumentoImportacao, ProcessoImportacao, STATUS_PROCESSO


class ProcessoListView(CustomListView):
    template_name = 'importacao/processo_list.html'
    model = ProcessoImportacao
    context_object_name = 'processos'
    success_url = reverse_lazy('importacao:listaprocessosview')
    permission_codename = 'view_processoimportacao'
    list_prefetch_related = ('etapas',)

    def status_atual(self):
        status = self.request.GET.get('status', 'andamento')
        return status if status in dict(STATUS_PROCESSO) or status == 'todos' else 'andamento'

    def get_queryset(self):
        processos = ProcessoImportacao.objects.all()
        status = self.status_atual()
        if status != 'todos':
            processos = processos.filter(status=status)
        return processos

    def get_context_data(self, **kwargs):
        context = super(ProcessoListView, self).get_context_data(**kwargs)
        context['add_url'] = reverse_lazy('importacao:addprocessoview')
        context['status_atual'] = self.status_atual()
        context['filtros'] = list(STATUS_PROCESSO) + [('todos', 'Todos')]
        context['alertas'] = agente.regras_importacao(date.today())
        return context


class AdicionarProcessoView(CustomCreateView):
    form_class = ProcessoImportacaoForm
    template_name = 'importacao/processo_form.html'
    permission_codename = 'add_processoimportacao'

    def get_context_data(self, **kwargs):
        context = super(AdicionarProcessoView, self).get_context_data(**kwargs)
        context['title_complete'] = 'Novo processo de importação'
        context['return_url'] = reverse_lazy('importacao:listaprocessosview')
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            processo = form.save()
            messages.success(request, 'Processo <b>%s</b> criado. Preencha as datas das etapas.' % processo)
            return redirect(processo)
        return self.form_invalid(form)


class EditarProcessoView(CustomUpdateView):
    form_class = ProcessoImportacaoForm
    model = ProcessoImportacao
    template_name = 'importacao/processo_form.html'
    permission_codename = 'change_processoimportacao'

    def get_context_data(self, **kwargs):
        context = super(EditarProcessoView, self).get_context_data(**kwargs)
        context['title_complete'] = 'Editar %s' % self.object
        context['return_url'] = self.object.get_absolute_url()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            processo = form.save()
            processo.sincronizar()
            messages.success(request, 'Processo <b>%s</b> atualizado.' % processo)
            return redirect(processo)
        return self.form_invalid(form)


class ProcessoView(CustomView):
    """Tela do processo: cada secao (etapas, containers, custos, documentos) salva separadamente."""
    template_name = 'importacao/processo_detail.html'
    permission_codename = 'view_processoimportacao'

    def montar(self, request, processo, **vinculados):
        context = {
            'processo': processo,
            'etapas_formset': EtapaFormSet(instance=processo, prefix='etapas'),
            'containers_formset': ContainerFormSet(instance=processo, prefix='containers'),
            'custos_formset': CustoFormSet(instance=processo, prefix='custos'),
            'documentos_form': DocumentosForm(),
            'documentos': processo.documentos.all(),
        }
        context.update(vinculados)
        return render(request, self.template_name, context)

    def get(self, request, pk):
        return self.montar(request, get_object_or_404(ProcessoImportacao, pk=pk))

    def post(self, request, pk):
        if not request.user.has_perm('importacao.change_processoimportacao'):
            messages.warning(
                request, 'Usuário não tem permissão para realizar esta operação.', 'permission_warning')
            return redirect('base:index')

        processo = get_object_or_404(ProcessoImportacao, pk=pk)
        secao = request.POST.get('secao')
        formsets = {
            'etapas': (EtapaFormSet, 'etapas_formset', 'Etapas atualizadas.'),
            'containers': (ContainerFormSet, 'containers_formset', 'Containers atualizados.'),
            'custos': (CustoFormSet, 'custos_formset', 'Custos atualizados.'),
        }

        if secao in formsets:
            classe, nome, mensagem = formsets[secao]
            formset = classe(request.POST, instance=processo, prefix=secao)
            if not formset.is_valid():
                return self.montar(request, processo, **{nome: formset})
            formset.save()
        elif secao == 'documentos':
            remover = request.POST.get('remover', '')
            if remover:
                if remover.isdigit():
                    processo.documentos.filter(pk=remover).delete()
                mensagem = 'Documento removido.'
            else:
                form = DocumentosForm(request.POST, request.FILES)
                if not form.is_valid():
                    return self.montar(request, processo, documentos_form=form)
                for arquivo in form.cleaned_data['arquivos']:
                    processo.documentos.create(
                        tipo=form.cleaned_data['tipo'], arquivo=arquivo, nome=arquivo.name[:255])
                mensagem = 'Documentos enviados.'
        else:
            return redirect(processo)

        processo = ProcessoImportacao.objects.get(pk=pk)
        processo.sincronizar()
        messages.success(request, mensagem)
        return redirect('%s#%s' % (processo.get_absolute_url(), secao))


class DocumentoView(CustomView):
    permission_codename = 'view_processoimportacao'

    def get(self, request, pk):
        documento = get_object_or_404(DocumentoImportacao, pk=pk)
        extensao = documento.nome.rsplit('.', 1)[-1].lower()
        return FileResponse(documento.arquivo.open('rb'), filename=documento.nome,
                            as_attachment=extensao not in ('pdf', 'jpg', 'jpeg', 'png'))
