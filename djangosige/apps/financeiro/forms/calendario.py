# -*- coding: utf-8 -*-

from decimal import Decimal

from django import forms

from djangosige.apps.financeiro.models import ItemCalendario


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


class ItemCalendarioForm(forms.ModelForm):

    class Meta:
        model = ItemCalendario
        fields = ('data', 'descricao', 'valor', 'concluido', 'destaque')
        field_classes = {'valor': ValorField}
        widgets = {
            'data': forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control datepicker'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'data': 'Data',
            'descricao': 'Descrição',
            'valor': 'Valor (R$)',
            'concluido': 'Concluído',
            'destaque': 'Destacar em vermelho',
        }
        help_texts = {
            'valor': 'Pode ficar em branco enquanto o valor não for conhecido.',
        }


class ImportarCalendarioForm(forms.Form):
    arquivo = forms.FileField(
        label='Planilha do calendário (.xlsx)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'}))

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        if not arquivo.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('Envie um arquivo .xlsx.')
        if arquivo.size > 20 * 1024 * 1024:
            raise forms.ValidationError('O arquivo tem mais de 20 MB.')
        return arquivo
