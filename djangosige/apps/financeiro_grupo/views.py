# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import TransferenciaGrupo, ProprietarioGrupo, SaldoEmpresa
from djangosige.apps.cadastro.models import Empresa


@login_required
def dashboard(request):
    """Dashboard do Controle Financeiro entre Empresas"""
    
    # Filtros
    origem_id = request.GET.get('origem')
    destino_id = request.GET.get('destino')
    status = request.GET.get('status')
    
    # Query base
    transferencias = TransferenciaGrupo.objects.select_related(
        'empresa_origem', 'empresa_destino')
    
    # Aplicar filtros
    if origem_id:
        transferencias = transferencias.filter(empresa_origem_id=origem_id)
    if destino_id:
        transferencias = transferencias.filter(empresa_destino_id=destino_id)
    if status:
        transferencias = transferencias.filter(status=status)
    
    # Últimos 30 dias
    data_30d = date.today() - timedelta(days=30)
    transferencias_30d = TransferenciaGrupo.objects.filter(
        data__gte=data_30d
    )
    
    # Total em movimentação
    total_movimentacao = transferencias_30d.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Pendentes
    pendentes = TransferenciaGrupo.objects.filter(status='pendente')
    qtd_pendentes = pendentes.count()
    valor_pendentes = pendentes.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Empresas
    empresas = Empresa.objects.all()
    qtd_empresas = empresas.count()
    
    # Calcular empresa credora e devedora
    saldos_empresas = []
    for empresa in empresas:
        entradas = TransferenciaGrupo.objects.filter(
            empresa_destino=empresa,
            status='concluida'
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        saidas = TransferenciaGrupo.objects.filter(
            empresa_origem=empresa,
            status='concluida'
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        saldo = float(entradas) - float(saidas)
        saldos_empresas.append({
            'empresa': getattr(getattr(empresa, 'pessoa_jur_info', None), 'nome_fantasia', None) or empresa.nome_razao_social,
            'saldo': saldo
        })
    
    saldos_empresas.sort(key=lambda x: x['saldo'], reverse=True)
    
    empresa_credora = saldos_empresas[0]['empresa'] if saldos_empresas else 'N/A'
    saldo_credora = f"{saldos_empresas[0]['saldo']:,.2f}" if saldos_empresas else '0,00'
    
    empresa_devedora = saldos_empresas[-1]['empresa'] if saldos_empresas else 'N/A'
    saldo_devedora = f"{saldos_empresas[-1]['saldo']:,.2f}" if saldos_empresas else '0,00'
    
    # Proprietário
    try:
        proprietario = ProprietarioGrupo.objects.first()
        proprietario_nome = proprietario.nome if proprietario else 'N/A'
        proprietario_cpf = proprietario.cpf_formatado if proprietario else '***.***.***-**'
    except:
        proprietario_nome = 'N/A'
        proprietario_cpf = '***.***.***-**'
    
    # Matriz de fluxo
    matriz_fluxo = []
    totais_entrada = []
    
    for emp_origem in empresas:
        linha = {
            'empresa': (getattr(getattr(emp_origem, 'pessoa_jur_info', None), 'nome_fantasia', None) or emp_origem.nome_razao_social)[:15],
            'valores': [],
            'total': 0
        }
        
        for emp_destino in empresas:
            if emp_origem == emp_destino:
                valor = 0
            else:
                valor = TransferenciaGrupo.objects.filter(
                    empresa_origem=emp_origem,
                    empresa_destino=emp_destino,
                    status='concluida'
                ).aggregate(Sum('valor'))['valor__sum'] or 0
            
            linha['valores'].append(float(valor))
            linha['total'] += float(valor)
        
        matriz_fluxo.append(linha)
    
    # Totais entrada (por coluna)
    for idx in range(len(empresas)):
        total_entrada = sum(linha['valores'][idx] for linha in matriz_fluxo)
        totais_entrada.append(total_entrada)
    
    # Dados para gráficos
    fluxo_30d = transferencias_30d.filter(
        status='concluida'
    ).extra(
        select={'dia': 'DATE(data)'}
    ).values('dia').annotate(
        total=Sum('valor')
    ).order_by('dia')
    
    fluxo_labels = [(item['dia'].strftime('%d/%m') if hasattr(item['dia'], 'strftime') else '/'.join(str(item['dia']).split('-')[::-1][:2])) for item in fluxo_30d[:14]]
    fluxo_valores = [float(item['total']) for item in fluxo_30d[:14]]
    
    saldos_labels = [item['empresa'][:15] for item in saldos_empresas]
    saldos_valores = [item['saldo'] for item in saldos_empresas]
    
    context = {
        'transferencias': transferencias.order_by('-data')[:50],
        'empresas': empresas,
        
        # Stats
        'total_movimentacao': f'{total_movimentacao:,.2f}',
        'empresa_credora': empresa_credora,
        'saldo_credora': saldo_credora,
        'empresa_devedora': empresa_devedora,
        'saldo_devedora': saldo_devedora,
        'qtd_pendentes': qtd_pendentes,
        'valor_pendentes': f'{valor_pendentes:,.2f}',
        'proprietario_nome': proprietario_nome,
        'proprietario_cpf': proprietario_cpf,
        'qtd_empresas': qtd_empresas,
        
        # Matriz
        'matriz_fluxo': matriz_fluxo,
        'totais_entrada': totais_entrada,
        
        # Gráficos
        'fluxo_labels': json.dumps(fluxo_labels),
        'fluxo_valores': json.dumps(fluxo_valores),
        'saldos_labels': json.dumps(saldos_labels),
        'saldos_valores': json.dumps(saldos_valores),
    }
    
    return render(request, 'financeiro_grupo/dashboard.html', context)


def _formulario_transferencia(request, transferencia=None):
    from .forms import TransferenciaForm
    form = TransferenciaForm(request.POST or None, instance=transferencia)
    if request.method == 'POST' and form.is_valid():
        nova = form.save(commit=False)
        if not nova.usuario_id:
            nova.usuario = request.user
        nova.save()
        return redirect('financeiro_grupo:transferencia_detail', pk=nova.pk)
    return render(request, 'financeiro_grupo/form.html', {'form': form, 'transferencia': transferencia})


@login_required
def transferencia_add(request):
    """Adicionar nova transferência (entra como pendente; 'Confirmar' conclui)"""
    return _formulario_transferencia(request)


@login_required
def transferencia_edit(request, pk):
    """Editar transferência"""
    return _formulario_transferencia(request, get_object_or_404(TransferenciaGrupo, pk=pk))


@login_required
def transferencia_detail(request, pk):
    """Ver detalhes da transferência"""
    transferencia = get_object_or_404(TransferenciaGrupo, pk=pk)
    return render(request, 'financeiro_grupo/detail.html', {'transferencia': transferencia})


@login_required
def transferencia_confirmar(request, pk):
    """Confirmar transferência"""
    transferencia = get_object_or_404(TransferenciaGrupo, pk=pk)
    transferencia.status = 'concluida'
    transferencia.data_confirmacao = timezone.now()
    transferencia.save()
    return redirect('financeiro_grupo:dashboard')


@login_required
def relatorio(request):
    """Relatório de todas as transferências de um período, com totais"""
    from datetime import datetime as _dt
    hoje = date.today()
    def _data(nome, padrao):
        try:
            return _dt.strptime(request.GET.get(nome, ''), '%Y-%m-%d').date()
        except ValueError:
            return padrao
    inicio = _data('de', hoje.replace(month=1, day=1))
    fim = _data('ate', hoje)
    transferencias = TransferenciaGrupo.objects.filter(
        data__date__gte=inicio, data__date__lte=fim).select_related('empresa_origem', 'empresa_destino', 'usuario').order_by('-data')
    totais = {status: transferencias.filter(status=status).aggregate(t=Sum('valor'))['t'] or 0
              for status, _ in TransferenciaGrupo.STATUS_CHOICES}
    por_tipo = transferencias.filter(status='concluida').values('tipo').annotate(total=Sum('valor')).order_by('-total')
    nomes_tipo = dict(TransferenciaGrupo.TIPO_CHOICES)
    return render(request, 'financeiro_grupo/relatorio.html', {
        'transferencias': transferencias, 'inicio': inicio, 'fim': fim, 'totais': totais,
        'por_tipo': [{'tipo': nomes_tipo.get(t['tipo'], t['tipo']), 'total': t['total']} for t in por_tipo],
    })
