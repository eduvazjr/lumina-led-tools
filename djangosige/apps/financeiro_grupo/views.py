# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
import json

from django.views.decorators.http import require_POST

from .models import ExtratoBancario, TransferenciaGrupo, ProprietarioGrupo, SaldoEmpresa
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


# ---------------------------------------------------------------- extratos

def _nome_empresa(empresa):
    return getattr(getattr(empresa, 'pessoa_jur_info', None), 'nome_fantasia', None) or empresa.nome_razao_social


def _ultimos_meses(hoje, quantidade=12):
    """(ano, mês) dos últimos meses fechados, do mais antigo para o mais recente."""
    ano, mes = hoje.year, hoje.month
    meses = []
    for _ in range(quantidade):
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
        meses.append((ano, mes))
    return list(reversed(meses))


@login_required
def extratos(request):
    """Extratos bancários das empresas do grupo: o que já foi enviado e o que falta."""
    from .forms import MESES
    empresas = list(Empresa.objects.select_related('pessoa_jur_info').order_by('nome_razao_social'))
    todos = ExtratoBancario.objects.select_related('empresa', 'empresa__pessoa_jur_info', 'enviado_por')

    meses = list(reversed(_ultimos_meses(date.today())))  # mês mais recente primeiro
    enviados = set(todos.filter(ano__gte=meses[-1][0]).values_list('empresa_id', 'ano', 'mes'))
    nomes_mes = dict(MESES)
    cobertura = [{
        'empresa': empresa, 'nome': _nome_empresa(empresa),
        'meses': [{'ano': a, 'mes': m, 'ok': (empresa.pk, a, m) in enviados} for a, m in meses],
    } for empresa in empresas]
    faltando = sum(1 for linha in cobertura for c in linha['meses'] if not c['ok'])

    lista = todos
    empresa_id = request.GET.get('empresa') or ''
    ano = request.GET.get('ano') or ''
    if empresa_id.isdigit():
        lista = lista.filter(empresa_id=empresa_id)
    if ano.isdigit():
        lista = lista.filter(ano=ano)
    anos = sorted(set(todos.values_list('ano', flat=True)) | {date.today().year}, reverse=True)
    return render(request, 'financeiro_grupo/extratos.html', {
        'extratos': lista, 'cobertura': cobertura, 'faltando': faltando,
        'meses_cabecalho': [{'ano': a, 'mes': m, 'rotulo': '%s/%02d' % (nomes_mes[m][:3].lower(), a % 100)} for a, m in meses],
        'empresas': [(e.pk, _nome_empresa(e)) for e in empresas], 'anos': anos,
        'empresa_id': empresa_id, 'ano': ano, 'total_enviados': todos.count(),
        'bancos_usados': sorted(set(todos.values_list('banco', flat=True))),
    })


def _formulario_extrato(request, extrato=None):
    from django.contrib import messages
    from .forms import ExtratoForm
    inicial = {}
    if extrato is None:
        anterior = _ultimos_meses(date.today(), 1)[0]
        inicial = {'ano': request.GET.get('ano') or anterior[0], 'mes': request.GET.get('mes') or anterior[1],
                   'empresa': request.GET.get('empresa')}
    form = ExtratoForm(request.POST or None, request.FILES or None, instance=extrato, initial=inicial)
    if request.method == 'POST' and form.is_valid():
        novo = form.save(commit=False)
        enviado = request.FILES.get('arquivo')
        if enviado:
            if extrato is not None and extrato.arquivo:
                extrato.arquivo.delete(save=False)
            novo.nome_arquivo = enviado.name[:255]
            novo.tamanho = enviado.size
        if not novo.enviado_por_id:
            novo.enviado_por = request.user
        novo.save()
        messages.success(request, 'Extrato salvo.')
        return redirect('financeiro_grupo:extratos')
    return render(request, 'financeiro_grupo/extrato_form.html', {
        'form': form, 'extrato': extrato,
        'bancos_usados': sorted(set(ExtratoBancario.objects.values_list('banco', flat=True))),
    })


@login_required
def extrato_add(request):
    return _formulario_extrato(request)


@login_required
def extrato_edit(request, pk):
    return _formulario_extrato(request, get_object_or_404(ExtratoBancario, pk=pk))


@login_required
def extrato_baixar(request, pk):
    from django.http import FileResponse
    extrato = get_object_or_404(ExtratoBancario, pk=pk)
    return FileResponse(extrato.arquivo.open('rb'), filename=extrato.nome_arquivo,
                        as_attachment=extrato.extensao not in ('pdf', 'jpg', 'jpeg', 'png'))


@login_required
@require_POST
def extrato_remover(request, pk):
    from django.contrib import messages
    get_object_or_404(ExtratoBancario, pk=pk).delete()
    messages.success(request, 'Extrato removido.')
    return redirect('financeiro_grupo:extratos')
