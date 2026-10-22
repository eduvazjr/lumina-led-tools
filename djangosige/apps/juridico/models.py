# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from djangosige.apps.cadastro.models import Empresa


class Processo(models.Model):
    """Modelo para processos judiciais e administrativos"""
    
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('arquivado', 'Arquivado'),
        ('ganho', 'Ganho'),
        ('perdido', 'Perdido'),
        ('acordo', 'Acordo'),
        ('prescrito', 'Prescrito'),
    )
    
    RISCO_CHOICES = (
        ('alto', 'Alto'),
        ('medio', 'Médio'),
        ('baixo', 'Baixo'),
    )
    
    ORGAO_CHOICES = (
        ('trf', 'TRF - Tribunal Regional Federal'),
        ('tst', 'TST - Tribunal Superior do Trabalho'),
        ('tjsp', 'TJSP - Tribunal de Justiça SP'),
        ('stj', 'STJ - Superior Tribunal de Justiça'),
        ('stf', 'STF - Supremo Tribunal Federal'),
        ('tjrj', 'TJRJ - Tribunal de Justiça RJ'),
        ('tjmg', 'TJMG - Tribunal de Justiça MG'),
        ('outro', 'Outro'),
    )
    
    numero = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número do Processo'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='processos',
        verbose_name='Empresa'
    )
    descricao = models.TextField(
        verbose_name='Descrição/Objeto'
    )
    parte_contraria = models.CharField(
        max_length=255,
        verbose_name='Parte Contrária'
    )
    orgao = models.CharField(
        max_length=20,
        choices=ORGAO_CHOICES,
        verbose_name='Órgão/Tribunal'
    )
    tipo_processo = models.CharField(
        max_length=100,
        verbose_name='Tipo de Processo',
        help_text='Ex: Trabalhista, Tributário, Cível, etc.'
    )
    valor_causa = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        verbose_name='Valor da Causa'
    )
    nivel_risco = models.CharField(
        max_length=10,
        choices=RISCO_CHOICES,
        default='medio',
        verbose_name='Nível de Risco'
    )
    probabilidade_perda = models.IntegerField(
        default=50,
        verbose_name='Probabilidade de Perda (%)',
        help_text='0 a 100%'
    )
    data_distribuicao = models.DateField(
        verbose_name='Data de Distribuição'
    )
    proximo_prazo = models.DateField(
        null=True,
        blank=True,
        verbose_name='Próximo Prazo'
    )
    descricao_prazo = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Descrição do Prazo'
    )
    ultima_movimentacao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Última Movimentação'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name='Status'
    )
    advogado_responsavel = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Advogado Responsável'
    )
    diretoria_alertada = models.BooleanField(
        default=False,
        verbose_name='Diretoria Alertada'
    )
    data_alerta_diretoria = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data do Alerta'
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
        verbose_name = 'Processo Judicial/Administrativo'
        verbose_name_plural = 'Processos Judiciais/Administrativos'
        ordering = ['-data_distribuicao']
    
    def __str__(self):
        return f'{self.numero} - {self.parte_contraria}'
    
    @property
    def dias_prazo(self):
        """Calcula dias até o próximo prazo"""
        if not self.proximo_prazo:
            return None
        from datetime import date
        delta = self.proximo_prazo - date.today()
        return delta.days
    
    @property
    def prazo_vencido(self):
        """Verifica se o prazo está vencido"""
        if not self.proximo_prazo:
            return False
        from datetime import date
        return self.proximo_prazo < date.today()
    
    @property
    def valor_risco(self):
        """Calcula valor em risco (valor_causa * probabilidade_perda)"""
        return float(self.valor_causa) * (self.probabilidade_perda / 100.0)


class Prazo(models.Model):
    """Prazos processuais relacionados a processos"""
    
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('cumprido', 'Cumprido'),
        ('vencido', 'Vencido'),
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='prazos',
        verbose_name='Processo'
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name='Descrição do Prazo'
    )
    data_intimacao = models.DateField(
        verbose_name='Data da Intimação'
    )
    data_vencimento = models.DateField(
        verbose_name='Data de Vencimento'
    )
    data_cumprimento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Cumprimento'
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
    alerta_enviado = models.BooleanField(
        default=False,
        verbose_name='Alerta Enviado'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    
    class Meta:
        verbose_name = 'Prazo Processual'
        verbose_name_plural = 'Prazos Processuais'
        ordering = ['data_vencimento']
    
    def __str__(self):
        return f'{self.processo.numero} - {self.descricao} ({self.data_vencimento.strftime("%d/%m/%Y")})'
    
    @property
    def dias_restantes(self):
        """Calcula dias restantes até o vencimento"""
        from datetime import date
        delta = self.data_vencimento - date.today()
        return delta.days


class AlertaDiretoria(models.Model):
    """Alertas enviados para a diretoria sobre processos críticos"""
    
    TIPO_CHOICES = (
        ('novo_processo', 'Novo Processo Alto Risco'),
        ('prazo_critico', 'Prazo Crítico'),
        ('prazo_vencido', 'Prazo Vencido'),
        ('sentenca', 'Sentença Desfavorável'),
        ('parado', 'Processo Parado'),
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name='Processo'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Alerta'
    )
    mensagem = models.TextField(
        verbose_name='Mensagem'
    )
    enviado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Enviado em'
    )
    lido = models.BooleanField(
        default=False,
        verbose_name='Lido'
    )
    lido_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Lido em'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    
    class Meta:
        verbose_name = 'Alerta para Diretoria'
        verbose_name_plural = 'Alertas para Diretoria'
        ordering = ['-enviado_em']
    
    def __str__(self):
        return f'{self.get_tipo_display()} - {self.processo.numero}'


class DocumentoProcesso(models.Model):
    """Documentos anexados aos processos"""
    
    TIPO_CHOICES = (
        ('peticao', 'Petição'),
        ('sentenca', 'Sentença'),
        ('acordo', 'Acordo'),
        ('comprovante', 'Comprovante'),
        ('outro', 'Outro'),
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Processo'
    )
    titulo = models.CharField(
        max_length=255,
        verbose_name='Título'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='outro',
        verbose_name='Tipo'
    )
    arquivo = models.FileField(
        upload_to='juridico/documentos/',
        verbose_name='Arquivo'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuário'
    )
    
    class Meta:
        verbose_name = 'Documento do Processo'
        verbose_name_plural = 'Documentos dos Processos'
        ordering = ['-data_upload']
    
    def __str__(self):
        return f'{self.titulo} - {self.processo.numero}'
