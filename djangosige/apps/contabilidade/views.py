# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta

from .models import (
    ProcessoContabil, EntradaCliente, Legalizacao,
    DepartamentoPessoal, Funcionario, FolhaPagamento,
    Fiscal, ApuracaoTributos, ObrigacaoAcessoria,
    Contabil, LancamentoContabil, ConciliacaoBancaria, DemonstracaoResultado
)
from .forms import (
    ProcessoContabilForm, EntradaClienteForm, LegalizacaoForm,
    DepartamentoPessoalForm, FuncionarioForm, FolhaPagamentoForm,
    FiscalForm, ApuracaoTributosForm, ObrigacaoAcessoriaForm,
    ContabilForm, LancamentoContabilForm, ConciliacaoBancariaForm, DREForm
)


@login_required
def dashboard(request):
    """Dashboard principal do sistema de contabilidade"""
    
    # Estatísticas gerais
    total_processos = ProcessoContabil.objects.filter(ativo=True).count()
    processos_entrada = ProcessoContabil.objects.filter(status='entrada', ativo=True).count()
    processos_legalizacao = ProcessoContabil.objects.filter(status='legalizacao', ativo=True).count()
    processos_dp = ProcessoContabil.objects.filter(status='dp', ativo=True).count()
    processos_fiscal = ProcessoContabil.objects.filter(status='fiscal', ativo=True).count()
    processos_contabil = ProcessoContabil.objects.filter(status='contabil', ativo=True).count()
    processos_concluidos = ProcessoContabil.objects.filter(status='concluido').count()
    
    # Processos recentes
    processos_recentes = ProcessoContabil.objects.filter(ativo=True).order_by('-data_abertura')[:5]
    
    # Alertas e pendências
    hoje = datetime.now().date()
    proximos_7_dias = hoje + timedelta(days=7)
    
    obrigacoes_vencendo = ObrigacaoAcessoria.objects.filter(
        data_vencimento__range=[hoje, proximos_7_dias],
        entregue=False
    ).select_related('fiscal__processo')
    
    folhas_pendentes = FolhaPagamento.objects.filter(
        processada=False,
        data_pagamento__isnull=True
    ).select_related('dp__processo')
    
    context = {
        'total_processos': total_processos,
        'processos_entrada': processos_entrada,
        'processos_legalizacao': processos_legalizacao,
        'processos_dp': processos_dp,
        'processos_fiscal': processos_fiscal,
        'processos_contabil': processos_contabil,
        'processos_concluidos': processos_concluidos,
        'processos_recentes': processos_recentes,
        'obrigacoes_vencendo': obrigacoes_vencendo,
        'folhas_pendentes': folhas_pendentes,
    }
    
    return render(request, 'contabilidade/dashboard.html', context)


@login_required
def lista_processos(request):
    """Lista todos os processos contábeis"""
    
    status_filtro = request.GET.get('status', '')
    busca = request.GET.get('q', '')
    
    processos = ProcessoContabil.objects.filter(ativo=True).select_related('cliente', 'responsavel')
    
    if status_filtro:
        processos = processos.filter(status=status_filtro)
    
    if busca:
        processos = processos.filter(
            Q(numero_processo__icontains=busca) |
            Q(cliente__nome_razao_social__icontains=busca)
        )
    
    processos = processos.order_by('-data_abertura')
    
    context = {
        'processos': processos,
        'status_filtro': status_filtro,
        'busca': busca,
    }
    
    return render(request, 'contabilidade/lista_processos.html', context)


@login_required
def novo_processo(request):
    """Criar novo processo contábil"""
    
    if request.method == 'POST':
        form = ProcessoContabilForm(request.POST)
        if form.is_valid():
            processo = form.save(commit=False)
            processo.responsavel = request.user
            processo.save()
            form.save_m2m()  # Salvar equipe (ManyToMany)
            
            messages.success(request, 'Processo criado com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        form = ProcessoContabilForm()
    
    context = {'form': form}
    return render(request, 'contabilidade/novo_processo.html', context)


@login_required
def detalhe_processo(request, pk):
    """Detalhes de um processo contábil"""
    
    processo = get_object_or_404(ProcessoContabil, pk=pk)
    
    # Verificar quais módulos já foram iniciados
    tem_entrada = hasattr(processo, 'entrada')
    tem_legalizacao = hasattr(processo, 'legalizacao')
    tem_dp = hasattr(processo, 'dp')
    tem_fiscal = hasattr(processo, 'fiscal')
    tem_contabil = hasattr(processo, 'contabil')
    
    context = {
        'processo': processo,
        'tem_entrada': tem_entrada,
        'tem_legalizacao': tem_legalizacao,
        'tem_dp': tem_dp,
        'tem_fiscal': tem_fiscal,
        'tem_contabil': tem_contabil,
    }
    
    return render(request, 'contabilidade/detalhe_processo.html', context)


@login_required
def editar_processo(request, pk):
    """Editar processo contábil"""
    
    processo = get_object_or_404(ProcessoContabil, pk=pk)
    
    if request.method == 'POST':
        form = ProcessoContabilForm(request.POST, instance=processo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Processo atualizado com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        form = ProcessoContabilForm(instance=processo)
    
    context = {'form': form, 'processo': processo}
    return render(request, 'contabilidade/editar_processo.html', context)


# ==================== MÓDULO 1: ENTRADA DE CLIENTE ====================

@login_required
def entrada_cliente(request, processo_id):
    """Módulo de entrada de cliente"""
    
    processo = get_object_or_404(ProcessoContabil, pk=processo_id)
    
    try:
        entrada = processo.entrada
    except EntradaCliente.DoesNotExist:
        entrada = None
    
    if request.method == 'POST':
        if entrada:
            form = EntradaClienteForm(request.POST, instance=entrada)
        else:
            form = EntradaClienteForm(request.POST)
        
        if form.is_valid():
            entrada_obj = form.save(commit=False)
            if not entrada:
                entrada_obj.processo = processo
            entrada_obj.save()
            
            # Avançar processo para próxima etapa se concluída
            if entrada_obj.concluida and processo.status == 'entrada':
                processo.status = 'legalizacao'
                processo.save()
            
            messages.success(request, 'Entrada de cliente salva com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        if entrada:
            form = EntradaClienteForm(instance=entrada)
        else:
            form = EntradaClienteForm()
    
    context = {
        'processo': processo,
        'entrada': entrada,
        'form': form,
    }
    
    return render(request, 'contabilidade/entrada_cliente.html', context)


# ==================== MÓDULO 2: LEGALIZAÇÃO ====================

@login_required
def legalizacao(request, processo_id):
    """Módulo de legalização"""
    
    processo = get_object_or_404(ProcessoContabil, pk=processo_id)
    
    try:
        legal = processo.legalizacao
    except Legalizacao.DoesNotExist:
        legal = None
    
    if request.method == 'POST':
        if legal:
            form = LegalizacaoForm(request.POST, instance=legal)
        else:
            form = LegalizacaoForm(request.POST)
        
        if form.is_valid():
            legal_obj = form.save(commit=False)
            if not legal:
                legal_obj.processo = processo
            legal_obj.save()
            
            # Avançar processo para próxima etapa se regularizada
            if legal_obj.regularizada and processo.status == 'legalizacao':
                processo.status = 'dp'
                processo.save()
            
            messages.success(request, 'Legalização salva com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        if legal:
            form = LegalizacaoForm(instance=legal)
        else:
            form = LegalizacaoForm()
    
    context = {
        'processo': processo,
        'legalizacao': legal,
        'form': form,
    }
    
    return render(request, 'contabilidade/legalizacao.html', context)


# ==================== MÓDULO 3: DEPARTAMENTO PESSOAL ====================

@login_required
def departamento_pessoal(request, processo_id):
    """Módulo de departamento pessoal"""
    
    processo = get_object_or_404(ProcessoContabil, pk=processo_id)
    
    try:
        dp = processo.dp
    except DepartamentoPessoal.DoesNotExist:
        dp = None
    
    if request.method == 'POST':
        if dp:
            form = DepartamentoPessoalForm(request.POST, instance=dp)
        else:
            form = DepartamentoPessoalForm(request.POST)
        
        if form.is_valid():
            dp_obj = form.save(commit=False)
            if not dp:
                dp_obj.processo = processo
            dp_obj.save()
            
            # Avançar processo para próxima etapa se em dia
            if dp_obj.em_dia and processo.status == 'dp':
                processo.status = 'fiscal'
                processo.save()
            
            messages.success(request, 'Departamento Pessoal salvo com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        if dp:
            form = DepartamentoPessoalForm(instance=dp)
        else:
            form = DepartamentoPessoalForm()
    
    context = {
        'processo': processo,
        'dp': dp,
        'form': form,
    }
    
    return render(request, 'contabilidade/departamento_pessoal.html', context)


@login_required
def funcionarios(request, dp_id):
    """Gerenciar funcionários"""
    
    dp = get_object_or_404(DepartamentoPessoal, pk=dp_id)
    funcionarios_lista = dp.funcionarios.all().order_by('nome_completo')
    
    context = {
        'dp': dp,
        'processo': dp.processo,
        'funcionarios': funcionarios_lista,
    }
    
    return render(request, 'contabilidade/funcionarios.html', context)


@login_required
def folha_pagamento(request, dp_id):
    """Gerenciar folhas de pagamento"""
    
    dp = get_object_or_404(DepartamentoPessoal, pk=dp_id)
    folhas = dp.folhas.all().order_by('-ano_referencia', '-mes_referencia')
    
    context = {
        'dp': dp,
        'processo': dp.processo,
        'folhas': folhas,
    }
    
    return render(request, 'contabilidade/folha_pagamento.html', context)


# ==================== MÓDULO 4: FISCAL ====================

@login_required
def fiscal(request, processo_id):
    """Módulo fiscal"""
    
    processo = get_object_or_404(ProcessoContabil, pk=processo_id)
    
    try:
        fisc = processo.fiscal
    except Fiscal.DoesNotExist:
        fisc = None
    
    if request.method == 'POST':
        if fisc:
            form = FiscalForm(request.POST, instance=fisc)
        else:
            form = FiscalForm(request.POST)
        
        if form.is_valid():
            fisc_obj = form.save(commit=False)
            if not fisc:
                fisc_obj.processo = processo
            fisc_obj.save()
            
            # Avançar processo para próxima etapa se em dia
            if fisc_obj.em_dia and processo.status == 'fiscal':
                processo.status = 'contabil'
                processo.save()
            
            messages.success(request, 'Módulo Fiscal salvo com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        if fisc:
            form = FiscalForm(instance=fisc)
        else:
            form = FiscalForm()
    
    context = {
        'processo': processo,
        'fiscal': fisc,
        'form': form,
    }
    
    return render(request, 'contabilidade/fiscal.html', context)


@login_required
def apuracao_tributos(request, fiscal_id):
    """Gerenciar apurações de tributos"""
    
    fisc = get_object_or_404(Fiscal, pk=fiscal_id)
    apuracoes = fisc.apuracoes.all().order_by('-ano_referencia', '-mes_referencia')
    
    context = {
        'fiscal': fisc,
        'processo': fisc.processo,
        'apuracoes': apuracoes,
    }
    
    return render(request, 'contabilidade/apuracao_tributos.html', context)


@login_required
def obrigacoes_acessorias(request, fiscal_id):
    """Gerenciar obrigações acessórias"""
    
    fisc = get_object_or_404(Fiscal, pk=fiscal_id)
    obrigacoes = fisc.obrigacoes.all().order_by('data_vencimento')
    
    context = {
        'fiscal': fisc,
        'processo': fisc.processo,
        'obrigacoes': obrigacoes,
    }
    
    return render(request, 'contabilidade/obrigacoes_acessorias.html', context)


# ==================== MÓDULO 5: CONTÁBIL ====================

@login_required
def contabil(request, processo_id):
    """Módulo contábil"""
    
    processo = get_object_or_404(ProcessoContabil, pk=processo_id)
    
    try:
        cont = processo.contabil
    except Contabil.DoesNotExist:
        cont = None
    
    if request.method == 'POST':
        if cont:
            form = ContabilForm(request.POST, instance=cont)
        else:
            form = ContabilForm(request.POST)
        
        if form.is_valid():
            cont_obj = form.save(commit=False)
            if not cont:
                cont_obj.processo = processo
            cont_obj.save()
            
            # Marcar processo como concluído se em dia
            if cont_obj.em_dia and processo.status == 'contabil':
                processo.status = 'concluido'
                processo.data_conclusao = datetime.now()
                processo.save()
            
            messages.success(request, 'Módulo Contábil salvo com sucesso!')
            return redirect('contabilidade:detalhe_processo', pk=processo.pk)
    else:
        if cont:
            form = ContabilForm(instance=cont)
        else:
            form = ContabilForm()
    
    context = {
        'processo': processo,
        'contabil': cont,
        'form': form,
    }
    
    return render(request, 'contabilidade/contabil.html', context)


@login_required
def lancamentos_contabeis(request, contabil_id):
    """Gerenciar lançamentos contábeis"""
    
    cont = get_object_or_404(Contabil, pk=contabil_id)
    lancamentos = cont.lancamentos.all().order_by('-data_lancamento')
    
    context = {
        'contabil': cont,
        'processo': cont.processo,
        'lancamentos': lancamentos,
    }
    
    return render(request, 'contabilidade/lancamentos_contabeis.html', context)


@login_required
def conciliacao_bancaria(request, contabil_id):
    """Gerenciar conciliações bancárias"""
    
    cont = get_object_or_404(Contabil, pk=contabil_id)
    conciliacoes = cont.conciliacoes.all().order_by('-ano_referencia', '-mes_referencia')
    
    context = {
        'contabil': cont,
        'processo': cont.processo,
        'conciliacoes': conciliacoes,
    }
    
    return render(request, 'contabilidade/conciliacao_bancaria.html', context)


@login_required
def demonstracao_resultado(request, contabil_id):
    """Gerenciar DREs"""
    
    cont = get_object_or_404(Contabil, pk=contabil_id)
    dres = cont.dres.all().order_by('-ano_referencia', '-mes_referencia')
    
    context = {
        'contabil': cont,
        'processo': cont.processo,
        'dres': dres,
    }
    
    return render(request, 'contabilidade/demonstracao_resultado.html', context)


# ==================== RELATÓRIOS ====================

@login_required
def relatorios(request):
    """Página inicial de relatórios"""
    return render(request, 'contabilidade/relatorios.html')


@login_required
def relatorio_processos(request):
    """Relatório de processos"""
    
    # Agregações por status
    status_stats = ProcessoContabil.objects.values('status').annotate(
        total=Count('id')
    ).order_by('status')
    
    context = {
        'status_stats': status_stats,
    }
    
    return render(request, 'contabilidade/relatorio_processos.html', context)


@login_required
def relatorio_fiscal(request):
    """Relatório fiscal consolidado"""
    
    # Totais mensais de tributos
    apuracoes = ApuracaoTributos.objects.all().order_by('-ano_referencia', '-mes_referencia')[:12]
    
    context = {
        'apuracoes': apuracoes,
    }
    
    return render(request, 'contabilidade/relatorio_fiscal.html', context)
