# -*- coding: utf-8 -*-
from django import forms
from django.core.validators import FileExtensionValidator

from djangosige.apps.financeiro.forms.lancamento import (
    EXTENSOES_DOCUMENTO, VariosArquivosField, VariosArquivosInput, validar_tamanho_documento)


class AnexosForm(forms.Form):
    arquivos = VariosArquivosField(
        label='Arquivos',
        validators=[FileExtensionValidator(
            EXTENSOES_DOCUMENTO,
            message='O arquivo .%(extension)s não é aceito. Envie PDF, imagem (JPG ou PNG), XML, Word ou Excel.'),
            validar_tamanho_documento],
        widget=VariosArquivosInput(attrs={'accept': ','.join('.' + ext for ext in EXTENSOES_DOCUMENTO)}),
        error_messages={'required': 'Escolha ao menos um arquivo.'},
    )
