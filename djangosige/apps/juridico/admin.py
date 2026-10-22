# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import Processo, Prazo, AlertaDiretoria, DocumentoProcesso


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'parte_contraria', 'orgao', 'nivel_risco', 'valor_causa', 'status', 'proximo_prazo')
    list_filter = ('status', 'nivel_risco', 'orgao', 'tipo_processo')
    search_fields = ('numero', 'parte_contraria', 'descricao')
    date_hierarchy = 'data_distribuicao'
    ordering = ('-data_distribuicao',)
    readonly_fields = ('criado_em', 'atualizado_em', 'dias_prazo', 'prazo_vencido', 'valor_risco')
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'empresa', 'tipo_processo', 'orgao')
        }),
        ('Partes', {
            'fields': ('parte_contraria', 'advogado_responsavel')
        }),
        ('Detalhes', {
            'fields': ('descricao', 'valor_causa', 'probabilidade_perda')
        }),
        ('Risco', {
            'fields': ('nivel_risco', 'valor_risco')
        }),
        ('Prazos', {
            'fields': ('data_distribuicao', 'proximo_prazo', 'descricao_prazo', 'ultima_movimentacao', 'dias_prazo', 'prazo_vencido')
        }),
        ('Status', {
            'fields': ('status', 'observacoes')
        }),
        ('Alertas', {
            'fields': ('diretoria_alertada', 'data_alerta_diretoria')
        }),
        ('Metadata', {
            'fields': ('usuario', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Prazo)
class PrazoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'descricao', 'data_vencimento', 'status', 'dias_restantes')
    list_filter = ('status', 'data_vencimento')
    search_fields = ('processo__numero', 'descricao')
    date_hierarchy = 'data_vencimento'
    ordering = ('data_vencimento',)
    readonly_fields = ('criado_em', 'dias_restantes')


@admin.register(AlertaDiretoria)
class AlertaDiretoriaAdmin(admin.ModelAdmin):
    list_display = ('processo', 'tipo', 'enviado_em', 'lido')
    list_filter = ('tipo', 'lido', 'enviado_em')
    search_fields = ('processo__numero', 'mensagem')
    date_hierarchy = 'enviado_em'
    ordering = ('-enviado_em',)
    readonly_fields = ('enviado_em',)


@admin.register(DocumentoProcesso)
class DocumentoProcessoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'processo', 'tipo', 'data_upload', 'usuario')
    list_filter = ('tipo', 'data_upload')
    search_fields = ('titulo', 'processo__numero', 'descricao')
    date_hierarchy = 'data_upload'
    ordering = ('-data_upload',)
    readonly_fields = ('data_upload',)
