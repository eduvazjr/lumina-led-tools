# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import Processo, Prazo, AlertaDiretoria, DocumentoProcesso


@login_required
def dashboard(request):
    """Dashboard do Controle Jurídico"""
    
    # Filtros
    status = request.GET.get('status')
    risco = request.GET.get('risco')
    prazo_filtro = request.GET.get('prazo')
    
    # Query base
    processos = Processo.objects.all()
    
    # Aplicar filtros
    if status:
        processos = processos.filter(status=status)
    if risco:
        processos = processos.filter(nivel_risco=risco)
    
    if prazo_filtro == 'vencido':
        processos = processos.filter(
            proximo_prazo__lt=date.today(),
            status='ativo'
        )
    elif prazo_filtro == '7':
        processos = processos.filter(
            proximo_prazo__gte=date.today(),
            proximo_prazo__lte=date.today() + timedelta(days=7),
            status='ativo'
        )
    elif prazo_filtro == '30':
        processos = processos.filter(
            proximo_prazo__gte=date.today(),
            proximo_prazo__lte=date.today() + timedelta(days=30),
            status='ativo'
        )
    
    # Stats dashboard
    processos_ativos = Processo.objects.filter(status='ativo').count()
    
    # Prazos vencendo (7 dias)
    prazos_urgentes = Processo.objects.filter(
        status='ativo',
        proximo_prazo__gte=date.today(),
        proximo_prazo__lte=date.today() + timedelta(days=7)
    ).count()
    
    # Prazos vencidos
    prazos_vencidos = Processo.objects.filter(
        status='ativo',
        proximo_prazo__lt=date.today()
    ).count()
    
    # Alto risco
    processos_alto_risco = Processo.objects.filter(
        status='ativo',
        nivel_risco='alto'
    ).count()
    
    # Valor em risco
    processos_ativos_obj = Processo.objects.filter(status='ativo')
    valor_risco = sum(p.valor_risco for p in processos_ativos_obj)
    
    # Processos ganhos (12 meses)
    data_12m = date.today() - timedelta(days=365)
    processos_ganhos = Processo.objects.filter(
        status='ganho',
        atualizado_em__gte=data_12m
    ).count()
    
    # Alertas de prazos críticos (vencendo em 7 dias)
    alertas_prazos = []
    processos_criticos = Processo.objects.filter(
        status='ativo',
        proximo_prazo__gte=date.today(),
        proximo_prazo__lte=date.today() + timedelta(days=7)
    )
    
    for proc in processos_criticos:
        alertas_prazos.append({
            'processo_numero': proc.numero,
            'descricao': proc.descricao_prazo or 'Prazo processual',
            'dias_restantes': proc.dias_prazo
        })
    
    # Resultado pesquisa (se houver)
    resultado_pesquisa = request.session.pop('resultado_pesquisa', None)
    
    context = {
        'processos': processos.order_by('-data_distribuicao')[:50],
        
        # Stats
        'processos_ativos': processos_ativos,
        'prazos_urgentes': prazos_urgentes,
        'prazos_vencidos': prazos_vencidos,
        'processos_alto_risco': processos_alto_risco,
        'valor_risco': f'{valor_risco:,.2f}',
        'processos_ganhos': processos_ganhos,
        
        # Alertas
        'alertas_prazos': alertas_prazos[:5],
        
        # Pesquisa
        'resultado_pesquisa': resultado_pesquisa,
    }
    
    return render(request, 'juridico/dashboard.html', context)


@login_required
def processo_add(request):
    """Adicionar novo processo"""
    # TODO: Implementar formulário
    return redirect('juridico:dashboard')


@login_required
def processo_edit(request, pk):
    """Editar processo"""
    processo = get_object_or_404(Processo, pk=pk)
    # TODO: Implementar formulário
    return redirect('juridico:dashboard')


@login_required
def processo_detail(request, pk):
    """Ver detalhes do processo"""
    processo = get_object_or_404(Processo, pk=pk)
    prazos = processo.prazos.all()
    documentos = processo.documentos.all()
    alertas = processo.alertas.all()
    
    context = {
        'processo': processo,
        'prazos': prazos,
        'documentos': documentos,
        'alertas': alertas,
    }
    return render(request, 'juridico/detail.html', context)


@login_required
def alertar_diretoria(request, pk):
    """Criar alerta para diretoria sobre processo"""
    processo = get_object_or_404(Processo, pk=pk)
    
    # Determinar tipo de alerta
    if processo.nivel_risco == 'alto' and not processo.diretoria_alertada:
        tipo = 'novo_processo'
        mensagem = f'Novo processo de alto risco cadastrado: {processo.numero}'
    elif processo.prazo_vencido:
        tipo = 'prazo_vencido'
        mensagem = f'Prazo vencido no processo {processo.numero}: {processo.descricao_prazo}'
    elif processo.dias_prazo and processo.dias_prazo <= 3:
        tipo = 'prazo_critico'
        mensagem = f'Prazo crítico no processo {processo.numero}: {processo.dias_prazo} dias restantes'
    else:
        tipo = 'novo_processo'
        mensagem = f'Alerta sobre processo {processo.numero}'
    
    # Criar alerta
    alerta = AlertaDiretoria.objects.create(
        processo=processo,
        tipo=tipo,
        mensagem=mensagem,
        usuario=request.user
    )
    
    # Marcar processo como alertado
    processo.diretoria_alertada = True
    processo.data_alerta_diretoria = timezone.now()
    processo.save()
    
    return redirect('juridico:dashboard')


@login_required
def pesquisar_processos(request):
    """Pesquisar processos em órgãos governamentais"""
    if request.method == 'POST':
        orgao = request.POST.get('orgao')
        busca = request.POST.get('busca')
        
        # Simulação de pesquisa (integração real requer APIs específicas)
        resultado = f"""
        Pesquisa realizada em: {dict(Processo.ORGAO_CHOICES).get(orgao, orgao)}
        Termo buscado: {busca}
        
        IMPORTANTE: Esta é uma simulação.
        
        Para pesquisa real, você precisa:
        1. Acessar o portal do tribunal: 
           - TRF: https://www.trf3.jus.br/
           - TST: https://www.tst.jus.br/
           - TJSP: https://esaj.tjsp.jus.br/
        
        2. Ou integrar APIs oficiais (requer certificado digital)
        
        3. Ou usar serviços como JusBrasil API
        
        Após obter os dados, clique em "Importar para o Sistema".
        """
        
        request.session['resultado_pesquisa'] = resultado
    
    return redirect('juridico:dashboard')


@login_required
def relatorio_risco(request):
    """Relatório de riscos jurídicos"""
    # TODO: Implementar relatório PDF
    return redirect('juridico:dashboard')
