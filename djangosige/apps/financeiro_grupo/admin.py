# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import TransferenciaGrupo, ProprietarioGrupo, SaldoEmpresa


@admin.register(TransferenciaGrupo)
class TransferenciaGrupoAdmin(admin.ModelAdmin):
    list_display = ('empresa_origem', 'empresa_destino', 'valor', 'tipo', 'data', 'status')
    list_filter = ('status', 'tipo', 'data')
    search_fields = ('empresa_origem__nome_fantasia', 'empresa_destino__nome_fantasia', 'finalidade')
    date_hierarchy = 'data'
    ordering = ('-data',)
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Transferência', {
            'fields': ('empresa_origem', 'empresa_destino', 'valor', 'tipo')
        }),
        ('Detalhes', {
            'fields': ('finalidade', 'data', 'data_confirmacao', 'status')
        }),
        ('Documentação', {
            'fields': ('comprovante', 'observacoes')
        }),
        ('Metadata', {
            'fields': ('usuario', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProprietarioGrupo)
class ProprietarioGrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'email', 'telefone')
    search_fields = ('nome', 'cpf', 'email')
    readonly_fields = ('criado_em', 'atualizado_em')


@admin.register(SaldoEmpresa)
class SaldoEmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'data_referencia', 'saldo_entrada', 'saldo_saida', 'saldo_liquido')
    list_filter = ('data_referencia', 'empresa')
    date_hierarchy = 'data_referencia'
    ordering = ('-data_referencia', 'empresa')
    readonly_fields = ('criado_em',)
