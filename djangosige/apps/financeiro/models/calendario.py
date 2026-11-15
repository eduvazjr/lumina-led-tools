# -*- coding: utf-8 -*-

from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal

from .lancamento import TIPOS_PAGAMENTO_ESCOLHAS


class ItemCalendario(models.Model):
    data = models.DateField(db_index=True)
    tipo_pagamento = models.CharField(
        'Tipo de Pagamento', max_length=30, choices=TIPOS_PAGAMENTO_ESCOLHAS,
        blank=True, default='')
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, validators=[
                                MinValueValidator(Decimal('0.00'))])
    concluido = models.BooleanField(default=False)
    destaque = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Item do calendário financeiro"
        verbose_name_plural = "Itens do calendário financeiro"
        ordering = ['data', 'id']

    def __str__(self):
        return self.descricao


class ProgramacaoMes(models.Model):
    ano = models.PositiveIntegerField()
    mes = models.PositiveSmallIntegerField()
    texto = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "Programação do mês"
        unique_together = ('ano', 'mes')

    def __str__(self):
        return '%02d/%d' % (self.mes, self.ano)

