# -*- coding: utf-8 -*-

from decimal import Decimal

from django import forms
from django.core.validators import FileExtensionValidator
from django.forms import inlineformset_factory

from djangosige.apps.financeiro.forms.lancamento import (
    EXTENSOES_DOCUMENTO, VariosArquivosField, VariosArquivosInput, validar_tamanho_documento)

from .models import (
    ContainerImportacao, CustoImportacao, EtapaImportacao, ProcessoImportacao, TIPOS_DOCUMENTO)


class ValorField(forms.DecimalField):
    """Aceita valores no formato brasileiro (1.234,56) e exibe com virgula."""
    widget = forms.TextInput

    def to_python(self, value):
        if isinstance(value, str) and ',' in value:
            value = value.replace('.', '').replace(',', '.')
        return super(ValorField, self).to_python(value)

    def prepare_value(self, value):
        if isinstance(value, Decimal):
            return str(value).replace('.', ',')
        return value


def data_input():
    return forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker'})


class ProcessoImportacaoForm(forms.ModelForm):
    SECOES = (
        ('Ordem de compra e mercadoria', (
            'numero_ordem_compra', 'pedido_compra', 'exportador', 'pais_origem', 'mercadoria', 'ncm')),
        ('Transporte', (
            'modal', 'incoterm', 'porto_origem', 'porto_destino', 'armador', 'agente_carga',
            'numero_bl', 'free_time_dias', 'demurrage_diaria')),
        ('Desembaraço', ('despachante', 'numero_di', 'canal', 'status')),
        ('Valores da compra', (
            'moeda', 'taxa_cambio', 'valor_mercadoria', 'valor_frete', 'valor_seguro')),
        ('Observações', ('observacoes',)),
    )

    def __init__(self, *args, **kwargs):
        super(ProcessoImportacaoForm, self).__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault('class', 'form-control')
        if not self.instance.pk:
            del self.fields['status']

    def secoes(self):
        return [(titulo, [self[nome] for nome in campos if nome in self.fields])
                for titulo, campos in self.SECOES]

    class Meta:
        model = ProcessoImportacao
        fields = ('numero_ordem_compra', 'pedido_compra', 'exportador', 'pais_origem', 'mercadoria', 'ncm',
                  'modal', 'incoterm', 'porto_origem', 'porto_destino', 'armador', 'agente_carga', 'numero_bl',
                  'free_time_dias', 'demurrage_diaria', 'despachante', 'numero_di', 'canal', 'status',
                  'moeda', 'taxa_cambio', 'valor_mercadoria', 'valor_frete', 'valor_seguro', 'observacoes')
        field_classes = {
            'taxa_cambio': ValorField,
            'valor_mercadoria': ValorField,
            'valor_frete': ValorField,
            'valor_seguro': ValorField,
            'demurrage_diaria': ValorField,
        }
        widgets = {
            'taxa_cambio': forms.TextInput(),
            'valor_mercadoria': forms.TextInput(),
            'valor_frete': forms.TextInput(),
            'valor_seguro': forms.TextInput(),
            'demurrage_diaria': forms.TextInput(),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'numero_ordem_compra': 'Número da ordem de compra',
            'pedido_compra': 'Pedido de compra no sistema',
            'exportador': 'Exportador',
            'pais_origem': 'País de origem',
            'mercadoria': 'Mercadoria',
            'ncm': 'NCM',
            'modal': 'Modal',
            'incoterm': 'Incoterm',
            'porto_origem': 'Porto/aeroporto de origem',
            'porto_destino': 'Porto/aeroporto de destino',
            'armador': 'Armador / companhia',
            'agente_carga': 'Agente de carga',
            'numero_bl': 'Número do BL / AWB',
            'free_time_dias': 'Free time (dias)',
            'demurrage_diaria': 'Demurrage por dia, por container (R$)',
            'despachante': 'Despachante',
            'numero_di': 'Número da DI / DUIMP',
            'canal': 'Canal de parametrização',
            'status': 'Status',
            'moeda': 'Moeda',
            'taxa_cambio': 'Taxa de câmbio (R$)',
            'valor_mercadoria': 'Valor da mercadoria (moeda da compra)',
            'valor_frete': 'Frete internacional (moeda da compra)',
            'valor_seguro': 'Seguro internacional (moeda da compra)',
            'observacoes': 'Observações',
        }


class EtapaForm(forms.ModelForm):

    class Meta:
        model = EtapaImportacao
        fields = ('data_prevista', 'data_realizada', 'nao_aplica', 'observacao')
        widgets = {
            'data_prevista': data_input(),
            'data_realizada': data_input(),
            'observacao': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ContainerForm(forms.ModelForm):

    class Meta:
        model = ContainerImportacao
        fields = ('numero', 'tipo', 'lacre', 'data_retirada',
                  'data_devolucao', 'local_devolucao')
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'lacre': forms.TextInput(attrs={'class': 'form-control'}),
            'data_retirada': data_input(),
            'data_devolucao': data_input(),
            'local_devolucao': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustoForm(forms.ModelForm):

    class Meta:
        model = CustoImportacao
        fields = ('tipo', 'descricao', 'valor', 'data_vencimento', 'pago')
        field_classes = {'valor': ValorField}
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
            'data_vencimento': data_input(),
        }


class DocumentosForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=TIPOS_DOCUMENTO, label='Tipo', widget=forms.Select(attrs={'class': 'form-control'}))
    arquivos = VariosArquivosField(
        label='Arquivos',
        help_text='PDF, imagem, XML, Word ou Excel, até 10 MB por arquivo.',
        validators=[FileExtensionValidator(EXTENSOES_DOCUMENTO), validar_tamanho_documento],
        widget=VariosArquivosInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': ','.join('.' + ext for ext in EXTENSOES_DOCUMENTO)}))


EtapaFormSet = inlineformset_factory(
    ProcessoImportacao, EtapaImportacao, form=EtapaForm, extra=0, can_delete=False)
ContainerFormSet = inlineformset_factory(
    ProcessoImportacao, ContainerImportacao, form=ContainerForm, extra=1, can_delete=True)
CustoFormSet = inlineformset_factory(
    ProcessoImportacao, CustoImportacao, form=CustoForm, extra=1, can_delete=True)
