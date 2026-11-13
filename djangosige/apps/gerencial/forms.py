# -*- coding: utf-8 -*-
from django import forms
from django.core.validators import FileExtensionValidator

from djangosige.apps.base.campos import DataInput, ValorBRField

from .models import PagamentoNegociacao

EXTENSOES_COMPROVANTE = ('pdf', 'jpg', 'jpeg', 'png', 'webp')
TAMANHO_MAXIMO = 10 * 1024 * 1024


class PagamentoNegociacaoForm(forms.ModelForm):
    data = forms.DateField(label='Data do pagamento', widget=DataInput(), input_formats=['%Y-%m-%d', '%d/%m/%Y'])
    valor = ValorBRField(label='Valor pago', max_digits=16, decimal_places=2, min_value=0.01)
    comprovante = forms.FileField(
        label='Comprovante', required=False,
        help_text='PDF ou foto do comprovante, até 10 MB.',
        validators=[FileExtensionValidator(
            EXTENSOES_COMPROVANTE, message='O arquivo .%(extension)s não é aceito. Envie PDF ou foto (JPG, PNG).')],
        widget=forms.ClearableFileInput(attrs={'accept': ','.join('.' + e for e in EXTENSOES_COMPROVANTE)}))

    class Meta:
        model = PagamentoNegociacao
        fields = ('fornecedor', 'pedido', 'data', 'valor', 'comprovante', 'observacao')
        widgets = {'fornecedor': forms.TextInput(attrs={'list': 'fornecedores-planilha', 'autocomplete': 'off'}),
                   'pedido': forms.TextInput(attrs={'placeholder': 'Opcional'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.comprovante:
            self.fields['comprovante'].help_text = ('Já tem comprovante (%s). Envie outro só para trocar.'
                                                   % self.instance.nome_comprovante)

    def clean_comprovante(self):
        arquivo = self.cleaned_data.get('comprovante')
        if arquivo and getattr(arquivo, 'size', 0) > TAMANHO_MAXIMO:
            raise forms.ValidationError('O comprovante tem mais de 10 MB.')
        return arquivo
