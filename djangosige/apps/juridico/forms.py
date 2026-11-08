# -*- coding: utf-8 -*-
from django import forms

from djangosige.apps.base.campos import DataInput, ValorBRField

from .models import Processo


class ProcessoForm(forms.ModelForm):
    valor_causa = ValorBRField(label='Valor da causa (R$)', max_digits=15, decimal_places=2, min_value=0, required=False)

    class Meta:
        model = Processo
        fields = ('numero', 'empresa', 'parte_contraria', 'orgao', 'tipo_processo', 'descricao',
                  'valor_causa', 'nivel_risco', 'probabilidade_perda', 'status',
                  'data_distribuicao', 'proximo_prazo', 'descricao_prazo', 'ultima_movimentacao',
                  'advogado_responsavel', 'observacoes')
        labels = {
            'numero': 'Número do processo', 'parte_contraria': 'Parte contrária', 'orgao': 'Órgão',
            'tipo_processo': 'Tipo de processo', 'descricao': 'Descrição', 'nivel_risco': 'Nível de risco',
            'probabilidade_perda': 'Chance de perda (%)', 'status': 'Situação',
            'data_distribuicao': 'Data de distribuição', 'proximo_prazo': 'Próximo prazo',
            'descricao_prazo': 'O que vence no próximo prazo', 'ultima_movimentacao': 'Última movimentação',
            'advogado_responsavel': 'Advogado responsável', 'observacoes': 'Observações',
        }
        widgets = {
            'data_distribuicao': DataInput(), 'proximo_prazo': DataInput(), 'ultima_movimentacao': DataInput(),
            'descricao': forms.Textarea(attrs={'rows': 3}), 'observacoes': forms.Textarea(attrs={'rows': 3}),
            'probabilidade_perda': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

    def clean_valor_causa(self):
        return self.cleaned_data.get('valor_causa') or 0

    def clean_probabilidade_perda(self):
        valor = self.cleaned_data.get('probabilidade_perda')
        if valor is not None and not 0 <= valor <= 100:
            raise forms.ValidationError('Informe um percentual entre 0 e 100.')
        return valor
