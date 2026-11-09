# -*- coding: utf-8 -*-
"""Pedidos dos marketplaces trazidos do Base.com (BaseLinker).

Os pedidos ficam guardados só pelos últimos dias (para acompanhar cancelamentos
e recalcular); o que as telas usam é o resumo por dia e por conta de venda,
que fica para sempre e ocupa pouco espaço.
"""
from django.db import models

PLATAFORMAS = {
    'melibr': 'Mercado Livre', 'shopeebr': 'Shopee', 'tiktokbr': 'TikTok Shop', 'amazon': 'Amazon',
    'temubr': 'Temu', 'personal': 'Venda direta / site', 'shop': 'Loja virtual',
}


class ContaCanal(models.Model):
    """Uma conta de venda no Base.com (ex.: ML - Led Tools, Shopee - MD Import)."""
    source_id = models.PositiveIntegerField(primary_key=True)
    origem = models.CharField(max_length=30)
    nome = models.CharField(max_length=120)
    comissao_percentual = models.DecimalField(
        'Comissão estimada (%)', max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Usada quando a plataforma não informa a comissão no pedido (Shopee, TikTok etc.).')

    class Meta:
        ordering = ['origem', 'nome']
        verbose_name = 'Conta de venda'
        verbose_name_plural = 'Contas de venda'

    def __str__(self):
        return self.nome

    @property
    def plataforma(self):
        return PLATAFORMAS.get(self.origem, self.origem)


class StatusPedidoBase(models.Model):
    status_id = models.PositiveIntegerField(primary_key=True)
    nome = models.CharField(max_length=120)
    cancelado = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class PedidoCanal(models.Model):
    order_id = models.BigIntegerField(primary_key=True)
    conta = models.ForeignKey(ContaCanal, on_delete=models.CASCADE, related_name='pedidos')
    status_id = models.PositiveIntegerField(default=0)
    data = models.DateField(db_index=True)
    confirmado_em = models.BigIntegerField(default=0, db_index=True)  # unix, como vem da API
    valor_produtos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    frete_cliente = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    comissao = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    frete_vendedor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    custo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    custo_completo = models.BooleanField(default=True)
    unidades = models.PositiveIntegerField(default=0)
    cancelado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-confirmado_em']


class DevolucaoCanal(models.Model):
    return_id = models.BigIntegerField(primary_key=True)
    order_id = models.BigIntegerField(default=0)
    conta = models.ForeignKey(ContaCanal, on_delete=models.CASCADE, related_name='devolucoes')
    data = models.DateField(db_index=True)
    criada_em = models.BigIntegerField(default=0, db_index=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)


class CustoProdutoBase(models.Model):
    """Custo médio do produto no estoque do Base.com (average_cost)."""
    chave = models.CharField(max_length=60, primary_key=True)  # inventário:produto(ou variação)
    custo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    atualizado_em = models.DateTimeField(auto_now=True)


class ResumoDiarioCanal(models.Model):
    data = models.DateField(db_index=True)
    conta = models.ForeignKey(ContaCanal, on_delete=models.CASCADE, related_name='resumos')
    pedidos = models.PositiveIntegerField(default=0)
    unidades = models.PositiveIntegerField(default=0)
    vendas_brutas = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    frete_cliente = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    cancelados_qtd = models.PositiveIntegerField(default=0)
    cancelados_valor = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    devolucoes_qtd = models.PositiveIntegerField(default=0)
    devolucoes_valor = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    comissao_informada = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    base_sem_comissao = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    frete_vendedor = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    custo = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    pedidos_sem_custo = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('data', 'conta')
        ordering = ['-data']


class SincronizacaoBase(models.Model):
    iniciada_em = models.DateTimeField(auto_now_add=True)
    terminada_em = models.DateTimeField(null=True, blank=True)
    pedidos = models.PositiveIntegerField(default=0)
    devolucoes = models.PositiveIntegerField(default=0)
    chamadas = models.PositiveIntegerField(default=0)
    completa = models.BooleanField(default=False)
    erro = models.TextField(blank=True)

    class Meta:
        ordering = ['-iniciada_em']
