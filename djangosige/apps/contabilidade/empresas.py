# -*- coding: utf-8 -*-
"""Contabilidade interna das empresas do grupo.

Cada empresa (cadastro > Empresas) tem uma ficha contábil (ProcessoContabil),
criada na primeira vez que alguém abre a empresa. Dela saem as três áreas:
Fiscal (apurações e obrigações), Contábil (lançamentos, conciliações e DRE) e
Departamento pessoal (funcionários e folhas).
"""
from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from djangosige.apps.base.campos import DataInput, ValorBRField
from djangosige.apps.cadastro.models import Empresa

from .forms import (
    ApuracaoTributosForm, ConciliacaoBancariaForm, ContabilForm, DepartamentoPessoalForm,
    DREForm, FiscalForm, FolhaPagamentoForm, FuncionarioForm, LancamentoContabilForm,
    ObrigacaoAcessoriaForm)
from .models import (
    ApuracaoTributos, ConciliacaoBancaria, Contabil, DemonstracaoResultado, DepartamentoPessoal,
    Fiscal, FolhaPagamento, Funcionario, LancamentoContabil, ObrigacaoAcessoria, ProcessoContabil)


def nome_empresa(empresa):
    juridica = getattr(empresa, 'pessoa_jur_info', None)
    return getattr(juridica, 'nome_fantasia', None) or empresa.nome_razao_social


def ficha(empresa):
    """Ficha contábil da empresa, com as áreas Contábil e DP. A área Fiscal só
    existe depois que alguém informa o regime tributário."""
    processo, _ = ProcessoContabil.objects.get_or_create(
        empresa=empresa, defaults={'numero_processo': 'EMP-%d' % empresa.pk, 'status': 'contabil'})
    Contabil.objects.get_or_create(processo=processo)
    DepartamentoPessoal.objects.get_or_create(processo=processo)
    return processo


ROTULOS = {
    'sped_contribuicoes': 'SPED Contribuições', 'sped_ecd': 'SPED ECD', 'sped_fiscal': 'SPED Fiscal',
    'anexo_simples': 'Anexo do Simples', 'faturamento_mes': 'Faturamento do mês',
    'total_nf_emitidas': 'NF emitidas', 'total_nf_recebidas': 'NF recebidas',
}


def no_padrao_brasileiro(form):
    """Valores aceitam 1.234,56 e datas usam o calendário do navegador."""
    for nome, rotulo in ROTULOS.items():
        if nome in form.fields:
            form.fields[nome].label = rotulo
    for nome, campo in list(form.fields.items()):
        if isinstance(campo, forms.DecimalField) and not isinstance(campo, ValorBRField):
            form.fields[nome] = ValorBRField(
                label=campo.label, required=campo.required, max_digits=campo.max_digits,
                decimal_places=campo.decimal_places, help_text=campo.help_text, initial=campo.initial)
        elif isinstance(campo, forms.DateField) and not isinstance(campo, forms.DateTimeField):
            campo.widget = DataInput()
            campo.input_formats = ['%Y-%m-%d', '%d/%m/%Y']
    # Campos com valor padrão no banco (ex.: total de NF = 0) não precisam ser
    # preenchidos: em branco, salvam o padrão.
    for nome, campo in form.fields.items():
        try:
            campo_modelo = form._meta.model._meta.get_field(nome)
        except Exception:
            continue
        if campo.required and campo_modelo.has_default() and not callable(campo_modelo.default) \
                and not isinstance(campo, forms.BooleanField):
            campo.required = False
            padrao = campo_modelo.default
            setattr(form, 'clean_%s' % nome, (lambda n, p: lambda: p if form.cleaned_data.get(n) in (None, '') else form.cleaned_data[n])(nome, padrao))
    return form


# tipo: (rótulo, model, form, área de onde pendura, campo pai, ordenação)
TIPOS = {
    'apuracao': ('Apuração de tributos', ApuracaoTributos, ApuracaoTributosForm, 'fiscal', 'fiscal'),
    'obrigacao': ('Obrigação acessória', ObrigacaoAcessoria, ObrigacaoAcessoriaForm, 'fiscal', 'fiscal'),
    'lancamento': ('Lançamento contábil', LancamentoContabil, LancamentoContabilForm, 'contabil', 'contabil'),
    'conciliacao': ('Conciliação bancária', ConciliacaoBancaria, ConciliacaoBancariaForm, 'contabil', 'contabil'),
    'dre': ('Demonstração do resultado (DRE)', DemonstracaoResultado, DREForm, 'contabil', 'contabil'),
    'funcionario': ('Funcionário', Funcionario, FuncionarioForm, 'dp', 'dp'),
    'folha': ('Folha de pagamento', FolhaPagamento, FolhaPagamentoForm, 'dp', 'dp'),
}
AREAS = {
    'fiscal': ('Dados fiscais', Fiscal, FiscalForm),
    'contabil': ('Dados contábeis', Contabil, ContabilForm),
    'dp': ('Dados do departamento pessoal', DepartamentoPessoal, DepartamentoPessoalForm),
}


def _area(processo, area):
    try:
        return getattr(processo, area)
    except AttributeError:  # inclui RelatedObjectDoesNotExist
        return None


def _resumo(processo, hoje):
    fiscal, contabil, dp = _area(processo, 'fiscal'), _area(processo, 'contabil'), _area(processo, 'dp')
    return {
        'fiscal': fiscal,
        'tributos_a_pagar': (fiscal.apuracoes.filter(pago=False).aggregate(t=Sum('total_tributos'))['t'] or 0) if fiscal else 0,
        'obrigacoes_pendentes': fiscal.obrigacoes.filter(entregue=False).count() if fiscal else 0,
        'obrigacoes_vencidas': fiscal.obrigacoes.filter(entregue=False, data_vencimento__lt=hoje).count() if fiscal else 0,
        'lancamentos_mes': contabil.lancamentos.filter(data_lancamento__year=hoje.year, data_lancamento__month=hoje.month).count() if contabil else 0,
        'conciliacoes_pendentes': contabil.conciliacoes.filter(conciliada=False).count() if contabil else 0,
        'funcionarios_ativos': dp.funcionarios.filter(ativo=True).count() if dp else 0,
    }


@login_required
def painel(request):
    hoje = date.today()
    linhas = []
    for empresa in Empresa.objects.all().order_by('nome_razao_social'):
        processo = getattr(empresa, 'ficha_contabil', None)
        linhas.append({'empresa': empresa, 'nome': nome_empresa(empresa),
                       'resumo': _resumo(processo, hoje) if processo else None})
    totais = {
        'tributos_a_pagar': sum((l['resumo']['tributos_a_pagar'] for l in linhas if l['resumo']), 0),
        'obrigacoes_pendentes': sum(l['resumo']['obrigacoes_pendentes'] for l in linhas if l['resumo']),
        'obrigacoes_vencidas': sum(l['resumo']['obrigacoes_vencidas'] for l in linhas if l['resumo']),
        'funcionarios_ativos': sum(l['resumo']['funcionarios_ativos'] for l in linhas if l['resumo']),
    }
    return render(request, 'contabilidade/painel.html', {'linhas': linhas, 'totais': totais, 'hoje': hoje})


@login_required
def empresa(request, empresa_id):
    emp = get_object_or_404(Empresa, pk=empresa_id)
    processo = ficha(emp)
    hoje = date.today()
    fiscal, contabil, dp = _area(processo, 'fiscal'), processo.contabil, processo.dp
    return render(request, 'contabilidade/empresa.html', {
        'empresa': emp, 'nome': nome_empresa(emp), 'processo': processo, 'resumo': _resumo(processo, hoje),
        'fiscal': fiscal, 'contabil': contabil, 'dp': dp, 'hoje': hoje,
        'apuracoes': fiscal.apuracoes.order_by('-ano_referencia', '-mes_referencia')[:12] if fiscal else [],
        'obrigacoes': fiscal.obrigacoes.order_by('entregue', 'data_vencimento')[:20] if fiscal else [],
        'lancamentos': contabil.lancamentos.order_by('-data_lancamento', '-pk')[:15],
        'conciliacoes': contabil.conciliacoes.order_by('-ano_referencia', '-mes_referencia')[:12],
        'dres': contabil.dres.order_by('-ano_referencia', '-mes_referencia')[:12],
        'funcionarios': dp.funcionarios.order_by('-ativo', 'nome_completo'),
        'folhas': dp.folhas.order_by('-ano_referencia', '-mes_referencia')[:12],
    })


@login_required
def dados(request, empresa_id, area):
    if area not in AREAS:
        raise Http404
    emp = get_object_or_404(Empresa, pk=empresa_id)
    processo = ficha(emp)
    titulo, _, classe_form = AREAS[area]
    instancia = _area(processo, area)
    form = no_padrao_brasileiro(classe_form(request.POST or None, instance=instancia))
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.processo = processo
        obj.save()
        form.save_m2m()
        messages.success(request, '%s salvos.' % titulo)
        return redirect('%s#%s' % (_url_empresa(emp), area))
    return render(request, 'contabilidade/form_empresa.html', {
        'form': form, 'empresa': emp, 'nome': nome_empresa(emp), 'titulo': titulo, 'area': area})


def _url_empresa(emp):
    from django.urls import reverse
    return reverse('contabilidade:empresa', args=[emp.pk])


@login_required
def registro(request, empresa_id, tipo, pk=None):
    if tipo not in TIPOS:
        raise Http404
    emp = get_object_or_404(Empresa, pk=empresa_id)
    processo = ficha(emp)
    rotulo, modelo, classe_form, area, campo_pai = TIPOS[tipo]
    pai = _area(processo, area)
    if pai is None:
        messages.info(request, 'Preencha os dados fiscais da empresa antes de lançar apurações e obrigações.')
        return redirect('contabilidade:dados_empresa', empresa_id=emp.pk, area=area)
    instancia = get_object_or_404(modelo, pk=pk, **{campo_pai: pai}) if pk else None
    form = no_padrao_brasileiro(classe_form(request.POST or None, instance=instancia))
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        setattr(obj, campo_pai, pai)
        if hasattr(obj, 'usuario_id') and not obj.usuario_id:
            obj.usuario = request.user
        obj.save()
        form.save_m2m()
        messages.success(request, '%s salvo.' % rotulo)
        return redirect('%s#%s' % (_url_empresa(emp), area))
    return render(request, 'contabilidade/form_empresa.html', {
        'form': form, 'empresa': emp, 'nome': nome_empresa(emp), 'titulo': rotulo, 'area': area,
        'instancia': instancia, 'tipo': tipo})


@login_required
@require_POST
def remover_registro(request, empresa_id, tipo, pk):
    if tipo not in TIPOS:
        raise Http404
    emp = get_object_or_404(Empresa, pk=empresa_id)
    processo = ficha(emp)
    rotulo, modelo, _, area, campo_pai = TIPOS[tipo]
    pai = _area(processo, area)
    if pai is None:
        raise Http404
    get_object_or_404(modelo, pk=pk, **{campo_pai: pai}).delete()
    messages.success(request, '%s removido.' % rotulo)
    return redirect('%s#%s' % (_url_empresa(emp), area))
