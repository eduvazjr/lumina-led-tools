# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import PagamentoFornecedor, ImportacaoPlanilha
from djangosige.apps.cadastro.models import Fornecedor


@login_required
def dashboard(request):
    """Dashboard do Controle Gerencial"""
    
    # Filtros
    fornecedor_id = request.GET.get('fornecedor')
    status = request.GET.get('status')
    periodo = request.GET.get('periodo')
    
    # Query base
    pagamentos = PagamentoFornecedor.objects.all()
    
    # Aplicar filtros
    if fornecedor_id:
        pagamentos = pagamentos.filter(fornecedor_id=fornecedor_id)
    if status:
        pagamentos = pagamentos.filter(status=status)
    if periodo:
        data_limite = date.today() - timedelta(days=int(periodo))
        pagamentos = pagamentos.filter(data_emissao__gte=data_limite)
    
    # Cálculos dashboard
    pagamentos_pendentes = PagamentoFornecedor.objects.filter(status='pendente')
    
    # Total a pagar
    total_pagar = pagamentos_pendentes.aggregate(Sum('valor'))['valor__sum'] or 0
    qtd_fornecedores = pagamentos_pendentes.values('fornecedor').distinct().count()
    
    # Vencidos
    vencidos = pagamentos_pendentes.filter(data_vencimento__lt=date.today())
    qtd_vencidos = vencidos.count()
    valor_vencidos = vencidos.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Médias
    media_semanal = calcular_media_periodo(7)
    media_mensal = calcular_media_periodo(30)
    
    # Maior e menor dívida por fornecedor
    dividas_por_fornecedor = pagamentos_pendentes.values(
        'fornecedor__nome_razao_social'
    ).annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    if dividas_por_fornecedor:
        maior_divida = dividas_por_fornecedor.first()
        menor_divida = dividas_por_fornecedor.last()
        
        maior_divida_fornecedor = maior_divida['fornecedor__nome_razao_social']
        maior_divida_valor = maior_divida['total']
        maior_divida_percentual = (float(maior_divida_valor) / float(total_pagar) * 100) if total_pagar > 0 else 0
        
        menor_divida_fornecedor = menor_divida['fornecedor__nome_razao_social']
        menor_divida_valor = menor_divida['total']
        menor_divida_percentual = (float(menor_divida_valor) / float(total_pagar) * 100) if total_pagar > 0 else 0
    else:
        maior_divida_fornecedor = menor_divida_fornecedor = 'N/A'
        maior_divida_valor = menor_divida_valor = 0
        maior_divida_percentual = menor_divida_percentual = 0
    
    # Dados para gráficos
    grafico_labels = [item['fornecedor__nome_razao_social'][:20] for item in dividas_por_fornecedor[:10]]
    grafico_valores = [float(item['total']) for item in dividas_por_fornecedor[:10]]
    
    # Vencimentos próximos (30 dias)
    vencimentos_30d = pagamentos_pendentes.filter(
        data_vencimento__gte=date.today(),
        data_vencimento__lte=date.today() + timedelta(days=30)
    ).values('data_vencimento').annotate(
        total=Sum('valor')
    ).order_by('data_vencimento')[:7]
    
    vencimentos_labels = [item['data_vencimento'].strftime('%d/%m') for item in vencimentos_30d]
    vencimentos_valores = [float(item['total']) for item in vencimentos_30d]
    
    context = {
        'pagamentos': pagamentos[:50],
        'fornecedores': Fornecedor.objects.all(),
        
        # Stats
        'media_semanal': f'{media_semanal:,.2f}',
        'media_mensal': f'{media_mensal:,.2f}',
        'maior_divida_fornecedor': maior_divida_fornecedor,
        'maior_divida_valor': f'{maior_divida_valor:,.2f}',
        'maior_divida_percentual': f'{maior_divida_percentual:.1f}',
        'menor_divida_fornecedor': menor_divida_fornecedor,
        'menor_divida_valor': f'{menor_divida_valor:,.2f}',
        'menor_divida_percentual': f'{menor_divida_percentual:.1f}',
        'total_pagar': f'{total_pagar:,.2f}',
        'qtd_fornecedores': qtd_fornecedores,
        'qtd_vencidos': qtd_vencidos,
        'valor_vencidos': f'{valor_vencidos:,.2f}',
        
        # Gráficos
        'grafico_labels': json.dumps(grafico_labels),
        'grafico_valores': json.dumps(grafico_valores),
        'vencimentos_labels': json.dumps(vencimentos_labels),
        'vencimentos_valores': json.dumps(vencimentos_valores),
    }
    
    return render(request, 'gerencial/dashboard.html', context)


def calcular_media_periodo(dias):
    """Calcula média de pagamentos em um período"""
    data_inicio = date.today() - timedelta(days=dias)
    total = PagamentoFornecedor.objects.filter(
        data_pagamento__gte=data_inicio,
        status='pago'
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    return float(total) / (dias / 7) if dias >= 7 else float(total)


@login_required
def pagamento_add(request):
    """Adicionar novo pagamento"""
    # TODO: Implementar formulário de criação
    return redirect('gerencial:dashboard')


@login_required
def pagamento_edit(request, pk):
    """Editar pagamento"""
    pagamento = get_object_or_404(PagamentoFornecedor, pk=pk)
    # TODO: Implementar formulário de edição
    return redirect('gerencial:dashboard')


@login_required
def pagamento_delete(request, pk):
    """Excluir pagamento"""
    pagamento = get_object_or_404(PagamentoFornecedor, pk=pk)
    pagamento.delete()
    return redirect('gerencial:dashboard')


@login_required
def pagamento_pagar(request, pk):
    """Marcar pagamento como pago"""
    pagamento = get_object_or_404(PagamentoFornecedor, pk=pk)
    pagamento.status = 'pago'
    pagamento.data_pagamento = date.today()
    pagamento.save()
    return redirect('gerencial:dashboard')


@login_required
def importar_planilha(request):
    """Importar planilha de pagamentos"""
    from django.contrib import messages
    from decimal import Decimal
    import csv
    import io
    
    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']
        
        # Validar extensão
        if not arquivo.name.endswith(('.csv', '.xlsx', '.xls')):
            messages.error(request, 'Formato inválido! Use .csv, .xlsx ou .xls')
            return redirect('gerencial:dashboard')
        
        try:
            registros_importados = 0
            registros_erro = 0
            log_erros = []
            
            # Processar CSV
            if arquivo.name.endswith('.csv'):
                decoded_file = arquivo.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string, delimiter=';')
                
                for linha_num, row in enumerate(reader, start=2):
                    try:
                        # Buscar fornecedor (por CNPJ ou nome)
                        fornecedor_busca = row.get('fornecedor_cnpj') or row.get('fornecedor_nome')
                        if not fornecedor_busca:
                            raise ValueError("Fornecedor não informado")
                        
                        fornecedor = Fornecedor.objects.filter(
                            Q(cnpj__icontains=fornecedor_busca) | 
                            Q(nome_razao_social__icontains=fornecedor_busca)
                        ).first()
                        
                        if not fornecedor:
                            raise ValueError(f"Fornecedor '{fornecedor_busca}' não encontrado")
                        
                        # Converter valor
                        valor_str = row.get('valor', '0').replace('.', '').replace(',', '.')
                        valor = Decimal(valor_str)
                        
                        # Converter datas
                        from datetime import datetime
                        data_emissao = datetime.strptime(row.get('data_emissao', ''), '%d/%m/%Y').date()
                        data_vencimento = datetime.strptime(row.get('data_vencimento', ''), '%d/%m/%Y').date()
                        
                        # Criar pagamento
                        PagamentoFornecedor.objects.create(
                            fornecedor=fornecedor,
                            descricao=row.get('descricao', f'Importado - {arquivo.name}'),
                            valor=valor,
                            data_emissao=data_emissao,
                            data_vencimento=data_vencimento,
                            status='pendente',
                            observacoes=row.get('observacoes', ''),
                            usuario=request.user
                        )
                        
                        registros_importados += 1
                        
                    except Exception as e:
                        registros_erro += 1
                        log_erros.append(f"Linha {linha_num}: {str(e)}")
            
            # Processar Excel
            elif arquivo.name.endswith(('.xlsx', '.xls')):
                try:
                    import openpyxl
                    from datetime import datetime
                    
                    wb = openpyxl.load_workbook(arquivo)
                    ws = wb.active
                    
                    # Pular cabeçalho
                    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                        try:
                            if not row[0]:  # Linha vazia
                                continue
                            
                            # Buscar fornecedor
                            fornecedor_busca = row[0]  # Primeira coluna: CNPJ ou nome
                            fornecedor = Fornecedor.objects.filter(
                                Q(cnpj__icontains=str(fornecedor_busca)) | 
                                Q(nome_razao_social__icontains=str(fornecedor_busca))
                            ).first()
                            
                            if not fornecedor:
                                raise ValueError(f"Fornecedor '{fornecedor_busca}' não encontrado")
                            
                            # Colunas esperadas: fornecedor, descricao, valor, data_emissao, data_vencimento, observacoes
                            descricao = row[1] if len(row) > 1 else f'Importado - {arquivo.name}'
                            valor = Decimal(str(row[2]).replace(',', '.')) if len(row) > 2 else Decimal('0')
                            
                            # Datas
                            if len(row) > 3 and row[3]:
                                data_emissao = row[3] if isinstance(row[3], date) else datetime.strptime(str(row[3]), '%d/%m/%Y').date()
                            else:
                                data_emissao = date.today()
                            
                            if len(row) > 4 and row[4]:
                                data_vencimento = row[4] if isinstance(row[4], date) else datetime.strptime(str(row[4]), '%d/%m/%Y').date()
                            else:
                                data_vencimento = date.today()
                            
                            observacoes = row[5] if len(row) > 5 else ''
                            
                            # Criar pagamento
                            PagamentoFornecedor.objects.create(
                                fornecedor=fornecedor,
                                descricao=descricao,
                                valor=valor,
                                data_emissao=data_emissao,
                                data_vencimento=data_vencimento,
                                status='pendente',
                                observacoes=observacoes,
                                usuario=request.user
                            )
                            
                            registros_importados += 1
                            
                        except Exception as e:
                            registros_erro += 1
                            log_erros.append(f"Linha {row_idx}: {str(e)}")
                    
                except ImportError:
                    messages.error(request, 'Biblioteca openpyxl não instalada! Execute: pip install openpyxl')
                    return redirect('gerencial:dashboard')
            
            # Registrar log da importação
            ImportacaoPlanilha.objects.create(
                arquivo=arquivo.name,
                registros_importados=registros_importados,
                registros_erro=registros_erro,
                log_erros='\n'.join(log_erros) if log_erros else '',
                usuario=request.user
            )
            
            # Mensagens
            if registros_importados > 0:
                messages.success(request, f'✅ {registros_importados} pagamento(s) importado(s) com sucesso!')
            
            if registros_erro > 0:
                messages.warning(request, f'⚠️ {registros_erro} registro(s) com erro. Verifique o log.')
            
        except Exception as e:
            messages.error(request, f'❌ Erro ao processar arquivo: {str(e)}')
    
    return redirect('gerencial:dashboard')
