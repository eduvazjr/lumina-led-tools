# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import PagamentoFornecedor, ImportacaoPlanilha


@admin.register(PagamentoFornecedor)
class PagamentoFornecedorAdmin(admin.ModelAdmin):
    list_display = ('fornecedor', 'valor', 'data_vencimento', 'status', 'dias_vencimento')
    list_filter = ('status', 'data_vencimento', 'fornecedor')
    search_fields = ('fornecedor__nome_razao_social', 'descricao')
    date_hierarchy = 'data_vencimento'
    ordering = ('-data_vencimento',)
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('fornecedor', 'descricao', 'valor')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_vencimento', 'data_pagamento')
        }),
        ('Status', {
            'fields': ('status', 'observacoes')
        }),
        ('Metadata', {
            'fields': ('usuario', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ImportacaoPlanilha)
class ImportacaoPlanilhaAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_importacao', 'registros_importados', 'registros_erro', 'usuario')
    list_filter = ('data_importacao',)
    search_fields = ('log_erros',)
    date_hierarchy = 'data_importacao'
    readonly_fields = ('data_importacao',)
