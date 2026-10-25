# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import (
    ProcessoContabil, EntradaCliente, Legalizacao,
    DepartamentoPessoal, Funcionario, FolhaPagamento,
    Fiscal, ApuracaoTributos, ObrigacaoAcessoria,
    Contabil, LancamentoContabil, ConciliacaoBancaria, DemonstracaoResultado
)


@admin.register(ProcessoContabil)
class ProcessoContabilAdmin(admin.ModelAdmin):
    list_display = ['numero_processo', 'cliente', 'status', 'responsavel', 'data_abertura', 'ativo']
    list_filter = ['status', 'ativo', 'data_abertura']
    search_fields = ['numero_processo', 'cliente__nome_razao_social']
    filter_horizontal = ['equipe']


@admin.register(EntradaCliente)
class EntradaClienteAdmin(admin.ModelAdmin):
    list_display = ['processo', 'data_contato_inicial', 'canal_contato', 'tipo_servico', 'proposta_aceita', 'concluida']
    list_filter = ['canal_contato', 'tipo_servico', 'proposta_aceita', 'concluida']


@admin.register(Legalizacao)
class LegalizacaoAdmin(admin.ModelAdmin):
    list_display = ['processo', 'tipo_operacao', 'cnpj', 'regularizada']
    list_filter = ['tipo_operacao', 'regularizada']
    search_fields = ['cnpj', 'numero_registro']


@admin.register(DepartamentoPessoal)
class DepartamentoPessoalAdmin(admin.ModelAdmin):
    list_display = ['processo', 'total_funcionarios', 'esocial_ativo', 'em_dia']
    list_filter = ['esocial_ativo', 'em_dia']


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'cpf', 'cargo', 'data_admissao', 'ativo']
    list_filter = ['ativo', 'data_admissao']
    search_fields = ['nome_completo', 'cpf']


@admin.register(FolhaPagamento)
class FolhaPagamentoAdmin(admin.ModelAdmin):
    list_display = ['dp', 'mes_referencia', 'ano_referencia', 'total_liquido', 'processada']
    list_filter = ['processada', 'ano_referencia', 'mes_referencia']


@admin.register(Fiscal)
class FiscalAdmin(admin.ModelAdmin):
    list_display = ['processo', 'regime_tributario', 'faturamento_mes', 'em_dia']
    list_filter = ['regime_tributario', 'em_dia']


@admin.register(ApuracaoTributos)
class ApuracaoTributosAdmin(admin.ModelAdmin):
    list_display = ['fiscal', 'mes_referencia', 'ano_referencia', 'receita_bruta', 'total_tributos', 'pago']
    list_filter = ['pago', 'ano_referencia', 'mes_referencia']


@admin.register(ObrigacaoAcessoria)
class ObrigacaoAcessoriaAdmin(admin.ModelAdmin):
    list_display = ['fiscal', 'tipo', 'mes_referencia', 'ano_referencia', 'data_vencimento', 'entregue']
    list_filter = ['tipo', 'entregue', 'ano_referencia']


@admin.register(Contabil)
class ContabilAdmin(admin.ModelAdmin):
    list_display = ['processo', 'plano_contas_implantado', 'ultima_conciliacao', 'em_dia']
    list_filter = ['plano_contas_implantado', 'em_dia']


@admin.register(LancamentoContabil)
class LancamentoContabilAdmin(admin.ModelAdmin):
    list_display = ['numero_lancamento', 'data_lancamento', 'tipo', 'valor', 'usuario']
    list_filter = ['tipo', 'data_lancamento']
    search_fields = ['numero_lancamento', 'historico']


@admin.register(ConciliacaoBancaria)
class ConciliacaoBancariaAdmin(admin.ModelAdmin):
    list_display = ['contabil', 'banco', 'mes_referencia', 'ano_referencia', 'conciliada']
    list_filter = ['conciliada', 'ano_referencia', 'banco']


@admin.register(DemonstracaoResultado)
class DemonstracaoResultadoAdmin(admin.ModelAdmin):
    list_display = ['contabil', 'mes_referencia', 'ano_referencia', 'receita_liquida', 'lucro_liquido']
    list_filter = ['ano_referencia', 'mes_referencia']
