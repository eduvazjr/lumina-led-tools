# -*- coding: utf-8 -*-
"""Campos de formulário no padrão brasileiro."""
from decimal import Decimal, InvalidOperation

from django import forms

from djangosige.apps.gerencial.templatetags.gerencial_format import ptbr_number


class ValorBRField(forms.DecimalField):
    """Aceita '1.234,56', '1234,56' ou '1234.56' e mostra 1.234,56."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.TextInput(attrs={'inputmode': 'decimal', 'placeholder': '0,00', 'autocomplete': 'off'}))
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            texto = value.replace('R$', '').replace(' ', '').strip()
            if ',' in texto:
                texto = texto.replace('.', '').replace(',', '.')
            value = texto
        return super().to_python(value)

    def prepare_value(self, value):
        if isinstance(value, (int, float, Decimal)):
            try:
                return ptbr_number(value, self.decimal_places if self.decimal_places is not None else 2)
            except (InvalidOperation, ValueError):
                return value
        return value


class DataInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%d')


class DataHoraInput(forms.DateTimeInput):
    input_type = 'datetime-local'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%dT%H:%M')
