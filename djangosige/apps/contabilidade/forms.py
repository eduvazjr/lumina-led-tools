# -*- coding: utf-8 -*-

from django import forms
from .models import (
    ProcessoContabil, EntradaCliente, Legalizacao,
    DepartamentoPessoal, Funcionario, FolhaPagamento,
    Fiscal, ApuracaoTributos, ObrigacaoAcessoria,
    Contabil, LancamentoContabil, ConciliacaoBancaria, DemonstracaoResultado
)


class ProcessoContabilForm(forms.ModelForm):
    class Meta:
        model = ProcessoContabil
        fields = ['cliente', 'empresa', 'numero_processo', 'status', 'equipe', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'equipe': forms.CheckboxSelectMultiple(),
        }


class EntradaClienteForm(forms.ModelForm):
    class Meta:
        model = EntradaCliente
        exclude = ['processo']
        widgets = {
            'data_contato_inicial': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'data_aceite': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'data_conclusao': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'informacoes_coletadas': forms.Textarea(attrs={'rows': 4}),
            'documentos_recebidos': forms.Textarea(attrs={'rows': 3}),
            'necessidades_identificadas': forms.Textarea(attrs={'rows': 4}),
            'escopo_definido': forms.Textarea(attrs={'rows': 4}),
        }


class LegalizacaoForm(forms.ModelForm):
    class Meta:
        model = Legalizacao
        exclude = ['processo']
        widgets = {
            'data_protocolo_junta': forms.DateInput(attrs={'type': 'date'}),
            'data_deferimento_junta': forms.DateInput(attrs={'type': 'date'}),
            'data_emissao_cnpj': forms.DateInput(attrs={'type': 'date'}),
            'data_inscricao_municipal': forms.DateInput(attrs={'type': 'date'}),
            'data_inscricao_estadual': forms.DateInput(attrs={'type': 'date'}),
            'data_alvara': forms.DateInput(attrs={'type': 'date'}),
            'data_conclusao': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'licencas_especiais': forms.Textarea(attrs={'rows': 3}),
            'cadastro_orgaos_reguladores': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class DepartamentoPessoalForm(forms.ModelForm):
    class Meta:
        model = DepartamentoPessoal
        exclude = ['processo']
        widgets = {
            'data_implantacao_esocial': forms.DateInput(attrs={'type': 'date'}),
            'ultima_folha_processada': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        exclude = ['dp']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'data_demissao': forms.DateInput(attrs={'type': 'date'}),
        }


class FolhaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FolhaPagamento
        exclude = ['dp', 'data_processamento']
        widgets = {
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
        }


class FiscalForm(forms.ModelForm):
    class Meta:
        model = Fiscal
        exclude = ['processo']
        widgets = {
            'ultima_apuracao': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class ApuracaoTributosForm(forms.ModelForm):
    class Meta:
        model = ApuracaoTributos
        exclude = ['fiscal', 'data_apuracao']
        widgets = {
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
        }


class ObrigacaoAcessoriaForm(forms.ModelForm):
    class Meta:
        model = ObrigacaoAcessoria
        exclude = ['fiscal']
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'data_entrega': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class ContabilForm(forms.ModelForm):
    class Meta:
        model = Contabil
        exclude = ['processo']
        widgets = {
            'data_implantacao_plano': forms.DateInput(attrs={'type': 'date'}),
            'ultima_conciliacao': forms.DateInput(attrs={'type': 'date'}),
            'ultima_dre': forms.DateInput(attrs={'type': 'date'}),
            'ultimo_balancete': forms.DateInput(attrs={'type': 'date'}),
            'ultimo_balanco': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class LancamentoContabilForm(forms.ModelForm):
    class Meta:
        model = LancamentoContabil
        exclude = ['contabil', 'data_registro', 'usuario']
        widgets = {
            'data_lancamento': forms.DateInput(attrs={'type': 'date'}),
            'historico': forms.Textarea(attrs={'rows': 3}),
        }


class ConciliacaoBancariaForm(forms.ModelForm):
    class Meta:
        model = ConciliacaoBancaria
        exclude = ['contabil']
        widgets = {
            'data_conciliacao': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'divergencias': forms.Textarea(attrs={'rows': 3}),
        }


class DREForm(forms.ModelForm):
    class Meta:
        model = DemonstracaoResultado
        exclude = ['contabil', 'data_geracao']
