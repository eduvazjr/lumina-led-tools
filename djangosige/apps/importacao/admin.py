# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import ProcessoImportacao


@admin.register(ProcessoImportacao)
class ProcessoImportacaoAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'exportador', 'mercadoria', 'modal', 'status')
    list_filter = ('status', 'modal')
    search_fields = ('referencia', 'exportador', 'numero_ordem_compra', 'numero_bl', 'numero_di')
