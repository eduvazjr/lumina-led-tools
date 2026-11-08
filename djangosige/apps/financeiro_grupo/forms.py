# -*- coding: utf-8 -*-
from django import forms
from django.utils import timezone

from djangosige.apps.base.campos import DataHoraInput, ValorBRField

from .models import TransferenciaGrupo


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
