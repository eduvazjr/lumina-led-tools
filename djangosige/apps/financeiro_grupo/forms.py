# -*- coding: utf-8 -*-
from django import forms
from django.core.validators import FileExtensionValidator
from django.utils import timezone

from djangosige.apps.base.campos import DataHoraInput, ValorBRField

from .models import ExtratoBancario, TransferenciaGrupo


class TransferenciaForm(forms.ModelForm):
    valor = ValorBRField(label='Valor (R$)', max_digits=16, decimal_places=2, min_value=0.01)
    data = forms.DateTimeField(label='Data da transferência', widget=DataHoraInput(),
                               input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M', '%d/%m/%Y'])

    class Meta:
        model = TransferenciaGrupo
        fields = ('empresa_origem', 'empresa_destino', 'valor', 'tipo', 'data', 'finalidade', 'observacoes')
        labels = {'empresa_origem': 'Empresa de origem', 'empresa_destino': 'Empresa de destino'}
        widgets = {'finalidade': forms.Textarea(attrs={'rows': 3}), 'observacoes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial.setdefault('data', timezone.localtime().replace(second=0, microsecond=0))

    def clean(self):
        dados = super().clean()
        if dados.get('empresa_origem') and dados.get('empresa_origem') == dados.get('empresa_destino'):
            self.add_error('empresa_destino', 'A empresa de destino precisa ser diferente da de origem.')
        return dados


EXTENSOES_EXTRATO = ('pdf', 'ofx', 'csv', 'txt', 'xls', 'xlsx', 'jpg', 'jpeg', 'png')
TAMANHO_MAXIMO_EXTRATO = 15 * 1024 * 1024
MESES = [(1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
         (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')]


class ExtratoForm(forms.ModelForm):
    mes = forms.TypedChoiceField(label='Mês', choices=MESES, coerce=int)
    ano = forms.IntegerField(label='Ano', min_value=2000, max_value=2100)
    saldo_final = ValorBRField(label='Saldo no fim do mês (opcional)', max_digits=16, decimal_places=2,
                               required=False, min_value=None)
    arquivo = forms.FileField(
        label='Arquivo do extrato',
        help_text='PDF, OFX, CSV, TXT, Excel ou foto, até 15 MB.',
        validators=[FileExtensionValidator(
            EXTENSOES_EXTRATO,
            message='O arquivo .%(extension)s não é aceito. Envie PDF, OFX, CSV, TXT, Excel ou foto (JPG, PNG).')],
        widget=forms.ClearableFileInput(attrs={'accept': ','.join('.' + e for e in EXTENSOES_EXTRATO)}),
    )

    class Meta:
        model = ExtratoBancario
        fields = ('empresa', 'banco', 'conta', 'mes', 'ano', 'saldo_final', 'arquivo', 'observacoes')
        widgets = {'observacoes': forms.Textarea(attrs={'rows': 2}),
                   'banco': forms.TextInput(attrs={'placeholder': 'Ex.: Itaú, Bradesco, Inter', 'list': 'bancos-usados'}),
                   'conta': forms.TextInput(attrs={'placeholder': 'Ex.: 1234 / 56789-0'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['arquivo'].required = False
            self.fields['arquivo'].help_text = 'Deixe em branco para manter o arquivo atual (%s).' % self.instance.nome_arquivo

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo and getattr(arquivo, 'size', 0) > TAMANHO_MAXIMO_EXTRATO:
            raise forms.ValidationError('O arquivo tem mais de 15 MB.')
        return arquivo
