# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import PagamentoFornecedor, ImportacaoPlanilha, PagamentoNegociacao
from . import calendario as cal
from .drive_negotiations import build_dashboard_data, load_negotiations
from djangosige.apps.cadastro.models import Fornecedor


@login_required
def dashboard(request):
    source = load_negotiations()
    supplier = request.GET.get('fornecedor', '').strip()
    all_records = source['records']
    records = [record for record in all_records if record.get('supplier') == supplier] if supplier else all_records
    dashboard_data = build_dashboard_data(records)
    consolidated = build_dashboard_data(all_records)
    context = dict(source)
    context.update(dashboard_data)
    context.update({
        'selected_supplier': supplier,
        'all_suppliers': consolidated['suppliers'],
        'consolidated_kpis': consolidated['kpis'],
        'chart_distribution_data': dashboard_data['chart_distribution'],
        'chart_due_data': dashboard_data['chart_due'],
    })
    hoje = timezone.localdate()
    ano, mes = cal.mes_pedido(request, hoje)
    pagamentos = PagamentoNegociacao.objects.select_related('usuario')
    if supplier:
        pagamentos = pagamentos.filter(fornecedor=supplier)
    calendario = cal.montar(records, pagamentos.filter(data__year__in=(ano - 1, ano, ano + 1)), ano, mes, hoje)
    context.update({
        'cal': calendario,
        'pagamentos_mes': pagamentos.filter(data__range=(calendario['inicio_mes'], calendario['fim_mes'])),
    })
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


# ------------------------------------------------- pagamentos com comprovante

def _voltar_calendario(fornecedor, data):
    from django.urls import reverse
    from urllib.parse import urlencode
    params = {'cal_ano': data.year, 'cal_mes': data.month}
    if fornecedor:
        params['fornecedor'] = fornecedor
    return '%s?%s#calendario' % (reverse('gerencial:dashboard'), urlencode(params))


def _form_pagamento_negociacao(request, pagamento=None):
    from django.contrib import messages
    from .forms import PagamentoNegociacaoForm
    inicial = {}
    if pagamento is None:
        inicial = {chave: request.GET.get(chave) for chave in ('fornecedor', 'pedido', 'valor', 'data')
                   if request.GET.get(chave)}
        inicial.setdefault('data', date.today())
    form = PagamentoNegociacaoForm(request.POST or None, request.FILES or None, instance=pagamento, initial=inicial)
    if request.method == 'POST' and form.is_valid():
        novo = form.save(commit=False)
        enviado = request.FILES.get('comprovante')
        if enviado:
            if pagamento is not None:
                anterior = PagamentoNegociacao.objects.get(pk=pagamento.pk).comprovante
                if anterior:
                    anterior.delete(save=False)
            novo.nome_comprovante = enviado.name[:255]
        if not novo.usuario_id:
            novo.usuario = request.user
        novo.save()
        messages.success(request, 'Pagamento salvo.')
        return redirect(_voltar_calendario(request.GET.get('filtro', ''), novo.data))
    fornecedores = load_negotiations().get('records', [])
    return render(request, 'gerencial/pagamento_negociacao_form.html', {
        'form': form, 'pagamento': pagamento,
        'fornecedores': sorted({r.get('supplier') for r in fornecedores if r.get('supplier')}),
    })


@login_required
def pagamento_negociacao_add(request):
    return _form_pagamento_negociacao(request)


@login_required
def pagamento_negociacao_edit(request, pk):
    return _form_pagamento_negociacao(request, get_object_or_404(PagamentoNegociacao, pk=pk))


@login_required
def pagamento_negociacao_comprovante(request, pk):
    from django.http import FileResponse, Http404
    pagamento = get_object_or_404(PagamentoNegociacao, pk=pk)
    if not pagamento.comprovante:
        raise Http404
    nome = pagamento.nome_comprovante or pagamento.comprovante.name.rsplit('/', 1)[-1]
    extensao = nome.rsplit('.', 1)[-1].lower() if '.' in nome else ''
    return FileResponse(pagamento.comprovante.open('rb'), filename=nome,
                        as_attachment=extensao not in ('pdf', 'jpg', 'jpeg', 'png', 'webp'))


@login_required
def pagamento_negociacao_remover(request, pk):
    from django.contrib import messages
    from django.http import HttpResponseNotAllowed
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    pagamento = get_object_or_404(PagamentoNegociacao, pk=pk)
    data = pagamento.data
    pagamento.delete()
    messages.success(request, 'Pagamento removido.')
    return redirect(_voltar_calendario('', data))
