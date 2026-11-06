# -*- coding: utf-8 -*-

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from djangosige.apps.base.custom_views import CustomCreateView, CustomUpdateView, CustomView
from djangosige.apps.financeiro.forms import ImportarCalendarioForm, ItemCalendarioForm
from djangosige.apps.financeiro.models import ItemCalendario, ProgramacaoMes, Saida

NOMES_MESES = ('', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto',
               'Setembro', 'Outubro', 'Novembro', 'Dezembro')
DIAS_SEMANA = ('Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado')


def url_do_mes(data):
    return '%s?ano=%d&mes=%d#dia-%s' % (
        reverse('financeiro:calendarioview'), data.year, data.month, data.isoformat())


def competencia_da_requisicao(request):
    hoje = date.today()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except ValueError:
        return hoje.year, hoje.month
    if not (2000 <= ano <= 2100 and 1 <= mes <= 12):
        return hoje.year, hoje.month
    return ano, mes


class CalendarioView(CustomView):
    template_name = 'financeiro/calendario/calendario.html'
    permission_codename = 'view_itemcalendario'

    def get(self, request):
        ano, mes = competencia_da_requisicao(request)
        hoje = date.today()
        semanas_mes = calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes)
        inicio, fim = semanas_mes[0][0], semanas_mes[-1][-1]

        itens = {}
        for item in ItemCalendario.objects.filter(data__range=(inicio, fim)):
            itens.setdefault(item.data, []).append(item)
        contas = {}
        for conta in Saida.objects.filter(data_vencimento__range=(inicio, fim), status__in=['1', '2']):
            contas.setdefault(conta.data_vencimento, []).append(conta)

        semanas = []
        for semana in semanas_mes:
            dias = []
            for dia in semana:
                do_dia = itens.get(dia, [])
                dias.append({
                    'data': dia,
                    'no_mes': dia.month == mes,
                    'hoje': dia == hoje,
                    'itens': do_dia,
                    'contas': contas.get(dia, []),
                    'total': sum((i.valor for i in do_dia if i.valor), Decimal('0.00')),
                    'atrasado': dia < hoje and any(not i.concluido for i in do_dia),
                })
            semanas.append(dias)

        resumo = ItemCalendario.objects.filter(data__year=ano, data__month=mes).aggregate(
            total=Sum('valor'),
            total_concluido=Sum('valor', filter=Q(concluido=True)),
            total_pendente=Sum('valor', filter=Q(concluido=False)),
            itens_pendentes=Count('id', filter=Q(concluido=False)),
            sem_valor=Count('id', filter=Q(concluido=False, valor__isnull=True)),
        )
        programacao = ProgramacaoMes.objects.filter(ano=ano, mes=mes).first()
        anterior = date(ano, mes, 1) - timedelta(days=1)
        proximo = date(ano, mes, 28) + timedelta(days=7)

        return render(request, self.template_name, {
            'ano': ano,
            'mes': mes,
            'nome_mes': NOMES_MESES[mes],
            'semanas': semanas,
            'dias_semana': DIAS_SEMANA,
            'resumo': resumo,
            'programacao': programacao.texto if programacao else '',
            'anterior': anterior,
            'proximo': proximo,
            'hoje': hoje,
        })


class AlternarItemCalendarioView(CustomView):
    permission_codename = 'change_itemcalendario'

    def post(self, request):
        item = get_object_or_404(ItemCalendario, pk=request.POST.get('item') or 0)
        item.concluido = not item.concluido
        item.save(update_fields=['concluido'])
        return redirect(url_do_mes(item.data))


class ProgramacaoMesView(CustomView):
    permission_codename = 'change_itemcalendario'

    def post(self, request):
        ano, mes = competencia_da_requisicao(request)
        ProgramacaoMes.objects.update_or_create(
            ano=ano, mes=mes, defaults={'texto': request.POST.get('texto', '')})
        messages.success(request, 'Programação salva.')
        return redirect('%s?ano=%d&mes=%d' % (reverse('financeiro:calendarioview'), ano, mes))


class ItemCalendarioFormMixin(object):
    form_class = ItemCalendarioForm
    template_name = 'financeiro/calendario/item_form.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if kwargs.get('pk') else None
        form = self.get_form()
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Item do calendário salvo.')
            return redirect(url_do_mes(item.data))
        return self.form_invalid(form)


class AdicionarItemCalendarioView(ItemCalendarioFormMixin, CustomCreateView):
    permission_codename = 'add_itemcalendario'

    def get_initial(self):
        initial = super(AdicionarItemCalendarioView, self).get_initial()
        try:
            initial['data'] = datetime.strptime(self.request.GET.get('data', ''), '%Y-%m-%d').date()
        except ValueError:
            initial['data'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super(AdicionarItemCalendarioView, self).get_context_data(**kwargs)
        context['title_complete'] = 'Adicionar item ao calendário'
        context['return_url'] = url_do_mes(self.get_initial()['data'])
        return context


class EditarItemCalendarioView(ItemCalendarioFormMixin, CustomUpdateView):
    model = ItemCalendario
    permission_codename = 'change_itemcalendario'

    def get_context_data(self, **kwargs):
        context = super(EditarItemCalendarioView, self).get_context_data(**kwargs)
        context['title_complete'] = 'Editar item do calendário'
        context['return_url'] = url_do_mes(self.object.data)
        return context


class RemoverItemCalendarioView(CustomView):
    permission_codename = 'delete_itemcalendario'

    def post(self, request, pk):
        item = get_object_or_404(ItemCalendario, pk=pk)
        data = item.data
        item.delete()
        messages.success(request, 'Item removido do calendário.')
        return redirect(url_do_mes(data))


class ImportarCalendarioView(CustomView):
    template_name = 'financeiro/calendario/importar.html'
    permission_codename = 'add_itemcalendario'

    def get(self, request):
        return render(request, self.template_name, {'form': ImportarCalendarioForm()})

    def post(self, request):
        from djangosige.apps.financeiro.planilha_calendario import importar_planilha

        form = ImportarCalendarioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                resumo, ignoradas = importar_planilha(form.cleaned_data['arquivo'])
            except ImportError:
                form.add_error('arquivo', 'A biblioteca openpyxl não está instalada no servidor.')
            except Exception:
                form.add_error('arquivo', 'Não foi possível ler esta planilha. Confira se é o arquivo do calendário.')
            else:
                texto = ('Importação concluída: %(meses)d meses, %(criados)d itens novos '
                         '(%(concluidos)d concluídos, %(sem_valor)d sem valor) e %(atualizados)d atualizados.' % {
                             'meses': resumo['meses'], 'criados': resumo['criados'],
                             'concluidos': resumo['concluidos'], 'sem_valor': resumo['sem_valor'],
                             'atualizados': resumo['atualizados']})
                if ignoradas:
                    texto += ' Abas não reconhecidas: %d.' % len(ignoradas)
                messages.success(request, texto)
                return redirect('financeiro:calendarioview')
        return render(request, self.template_name, {'form': form})
