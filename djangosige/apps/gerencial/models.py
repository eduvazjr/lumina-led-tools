# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from djangosige.apps.cadastro.models import Fornecedor


class PagamentoFornecedor(models.Model):
    """Modelo para controle de pagamentos a fornecedores"""
    
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    )
    
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        related_name='pagamentos',
        verbose_name='Fornecedor'
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name='Descrição'
    )
    valor = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='Valor'
    )
    data_emissao = models.DateField(
        verbose_name='Data de Emissão'
    )
    data_vencimento = models.DateField(
        verbose_name='Data de Vencimento'
    )
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Pagamento'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Pagamento a Fornecedor'
        verbose_name_plural = 'Pagamentos a Fornecedores'
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f'{self.fornecedor.nome_razao_social} - R$ {self.valor}'
    
    @property
    def dias_vencimento(self):
        """Calcula dias até o vencimento (negativo se vencido)"""
        from datetime import date
        delta = self.data_vencimento - date.today()
        return delta.days
    
    @property
    def percentual_total(self):
        """Calcula percentual sobre o total de pagamentos pendentes"""
        total = PagamentoFornecedor.objects.filter(
            status='pendente'
        ).aggregate(models.Sum('valor'))['valor__sum'] or 0
        
        if total > 0:
            return (float(self.valor) / float(total)) * 100
        return 0
    
    def save(self, *args, **kwargs):
        # Atualizar status automaticamente baseado na data
        from datetime import date
        if self.status == 'pendente' and self.data_vencimento < date.today():
            self.status = 'vencido'
        super().save(*args, **kwargs)


class ImportacaoPlanilha(models.Model):
    """Histórico de importações de planilhas"""
    
    arquivo = models.FileField(
        upload_to='gerencial/planilhas/',
        verbose_name='Arquivo'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    data_importacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Importação'
    )
    registros_importados = models.IntegerField(
        default=0,
        verbose_name='Registros Importados'
    )
    registros_erro = models.IntegerField(
        default=0,
        verbose_name='Registros com Erro'
    )
    log_erros = models.TextField(
        blank=True,
        verbose_name='Log de Erros'
    )
    
    class Meta:
        verbose_name = 'Importação de Planilha'
        verbose_name_plural = 'Importações de Planilhas'
        ordering = ['-data_importacao']
    
    def __str__(self):
        return f'Importação {self.id} - {self.data_importacao.strftime("%d/%m/%Y %H:%M")}'
