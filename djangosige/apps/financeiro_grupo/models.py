# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from djangosige.apps.cadastro.models import Empresa


class TransferenciaGrupo(models.Model):
    """Modelo para transferências financeiras entre empresas do grupo"""
    
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    )
    
    TIPO_CHOICES = (
        ('emprestimo', 'Empréstimo'),
        ('pagamento', 'Pagamento'),
        ('investimento', 'Investimento'),
        ('reembolso', 'Reembolso'),
        ('outro', 'Outro'),
    )
    
    empresa_origem = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='transferencias_saida',
        verbose_name='Empresa Origem'
    )
    empresa_destino = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='transferencias_entrada',
        verbose_name='Empresa Destino'
    )
    valor = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        verbose_name='Valor'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='outro',
        verbose_name='Tipo'
    )
    finalidade = models.TextField(
        verbose_name='Finalidade'
    )
    data = models.DateTimeField(
        verbose_name='Data da Transferência'
    )
    data_confirmacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Confirmação'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    comprovante = models.FileField(
        upload_to='financeiro_grupo/comprovantes/',
        null=True,
        blank=True,
        verbose_name='Comprovante'
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Responsável'
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
        verbose_name = 'Transferência entre Empresas'
        verbose_name_plural = 'Transferências entre Empresas'
        ordering = ['-data']
    
    def __str__(self):
        return f'{self.empresa_origem} → {self.empresa_destino} - R$ {self.valor}'
    
    @property
    def esta_concluida(self):
        return self.status == 'concluida'


class ProprietarioGrupo(models.Model):
    """Informações do proprietário do grupo empresarial"""
    
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome Completo'
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name='CPF'
    )
    email = models.EmailField(
        verbose_name='E-mail'
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefone'
    )
    endereco = models.TextField(
        blank=True,
        verbose_name='Endereço'
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
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
        verbose_name = 'Proprietário do Grupo'
        verbose_name_plural = 'Proprietários do Grupo'
    
    def __str__(self):
        return f'{self.nome} - CPF: {self.cpf}'
    
    @property
    def cpf_formatado(self):
        """Retorna CPF formatado: XXX.XXX.XXX-XX"""
        cpf = self.cpf.replace('.', '').replace('-', '')
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'


class SaldoEmpresa(models.Model):
    """Saldos das empresas do grupo (calculado periodicamente)"""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='saldos_historico',
        verbose_name='Empresa'
    )
    data_referencia = models.DateField(
        verbose_name='Data de Referência'
    )
    saldo_entrada = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='Total Entradas'
    )
    saldo_saida = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='Total Saídas'
    )
    saldo_liquido = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='Saldo Líquido'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    class Meta:
        verbose_name = 'Saldo de Empresa'
        verbose_name_plural = 'Saldos de Empresas'
        ordering = ['-data_referencia', 'empresa']
        unique_together = ('empresa', 'data_referencia')
    
    def __str__(self):
        return f'{self.empresa} - {self.data_referencia.strftime("%m/%Y")} - R$ {self.saldo_liquido}'
