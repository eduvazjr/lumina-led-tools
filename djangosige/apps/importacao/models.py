# -*- coding: utf-8 -*-

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse

from djangosige.apps.base.storage import DocumentosPrivadosStorage

ETAPAS = (
    ('ordem_compra', 'Ordem de compra emitida'),
    ('licenca', 'Licença de importação (LI)'),
    ('cambio', 'Câmbio / pagamento ao exportador'),
    ('booking', 'Reserva de praça (booking)'),
    ('embarque', 'Embarque na origem'),
    ('chegada', 'Chegada ao porto de destino'),
    ('registro', 'Registro da DI/DUIMP'),
    ('desembaraco', 'Desembaraço aduaneiro'),
    ('retirada', 'Retirada do porto'),
    ('entrega', 'Entrega no armazém'),
    ('devolucao', 'Devolução do container vazio'),
)

MODAIS = (
    ('maritimo', 'Marítimo'),
    ('aereo', 'Aéreo'),
    ('rodoviario', 'Rodoviário'),
)

INCOTERMS = tuple((i, i) for i in (
    'EXW', 'FCA', 'FAS', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP'))

MOEDAS = (
    ('USD', 'Dólar (USD)'),
    ('EUR', 'Euro (EUR)'),
    ('CNY', 'Yuan (CNY)'),
    ('GBP', 'Libra (GBP)'),
    ('BRL', 'Real (BRL)'),
)

CANAIS = (
    ('', 'Não parametrizado'),
    ('verde', 'Verde'),
    ('amarelo', 'Amarelo'),
    ('vermelho', 'Vermelho'),
    ('cinza', 'Cinza'),
)

STATUS_PROCESSO = (
    ('andamento', 'Em andamento'),
    ('concluido', 'Concluído'),
    ('cancelado', 'Cancelado'),
)

TIPOS_CONTAINER = (
    ('20dc', "20' Dry"),
    ('40dc', "40' Dry"),
    ('40hc', "40' High Cube"),
    ('20rf', "20' Reefer"),
    ('40rf', "40' Reefer"),
    ('outro', 'Outro'),
)

TIPOS_CUSTO = (
    ('ii', 'II'),
    ('ipi', 'IPI'),
    ('pis', 'PIS-Importação'),
    ('cofins', 'COFINS-Importação'),
    ('icms', 'ICMS'),
    ('afrmm', 'AFRMM'),
    ('siscomex', 'Taxa Siscomex'),
    ('thc', 'Capatazia / THC'),
    ('armazenagem', 'Armazenagem'),
    ('despachante', 'Despachante'),
    ('frete_nac', 'Frete nacional'),
    ('demurrage', 'Demurrage'),
    ('outro', 'Outros'),
)

TIPOS_DOCUMENTO = (
    ('ordem_compra', 'Ordem de compra'),
    ('proforma', 'Proforma invoice'),
    ('invoice', 'Commercial invoice'),
    ('packing', 'Packing list'),
    ('bl', 'BL / AWB'),
    ('li', 'Licença de importação'),
    ('di', 'DI / DUIMP'),
    ('origem', 'Certificado de origem'),
    ('nfe', 'NF-e de entrada'),
    ('outro', 'Outro'),
)

VALOR_MINIMO = [MinValueValidator(Decimal('0.00'))]


class ProcessoImportacao(models.Model):
    referencia = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(
        max_length=10, choices=STATUS_PROCESSO, default='andamento')

    numero_ordem_compra = models.CharField(max_length=60)
    pedido_compra = models.ForeignKey(
        'compras.PedidoCompra', related_name='processos_importacao', on_delete=models.SET_NULL, null=True, blank=True)
    exportador = models.CharField(max_length=255)
    pais_origem = models.CharField(max_length=80)
    mercadoria = models.CharField(max_length=255)
    ncm = models.CharField(max_length=10, blank=True, default='')

    modal = models.CharField(
        max_length=10, choices=MODAIS, default='maritimo')
    incoterm = models.CharField(
        max_length=3, choices=INCOTERMS, default='FOB')
    porto_origem = models.CharField(max_length=120, blank=True, default='')
    porto_destino = models.CharField(max_length=120, blank=True, default='')
    armador = models.CharField(max_length=120, blank=True, default='')
    agente_carga = models.CharField(max_length=120, blank=True, default='')
    despachante = models.CharField(max_length=120, blank=True, default='')
    numero_bl = models.CharField(max_length=60, blank=True, default='')
    numero_di = models.CharField(max_length=60, blank=True, default='')
    canal = models.CharField(max_length=10, choices=CANAIS,
                             blank=True, default='')

    moeda = models.CharField(max_length=3, choices=MOEDAS, default='USD')
    taxa_cambio = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal('1.0000'), validators=VALOR_MINIMO)
    valor_mercadoria = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=VALOR_MINIMO)
    valor_frete = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=VALOR_MINIMO)
    valor_seguro = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=VALOR_MINIMO)

    free_time_dias = models.PositiveIntegerField(default=7)
    demurrage_diaria = models.DecimalField(
        max_digits=13, decimal_places=2, default=Decimal('0.00'), validators=VALOR_MINIMO)

    observacoes = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Processo de importação'
        verbose_name_plural = 'Processos de importação'
        ordering = ['-id']

    def __str__(self):
        return self.referencia

    def save(self, *args, **kwargs):
        novo = self.pk is None
        if novo:
            self.referencia = uuid4().hex
        super(ProcessoImportacao, self).save(*args, **kwargs)
        if novo:
            self.referencia = 'IMP-%d-%04d' % (date.today().year, self.pk)
            ProcessoImportacao.objects.filter(
                pk=self.pk).update(referencia=self.referencia)
            EtapaImportacao.objects.bulk_create([
                EtapaImportacao(processo=self, codigo=codigo, ordem=ordem)
                for ordem, (codigo, _) in enumerate(ETAPAS)])
            self.sincronizar()

    def get_absolute_url(self):
        return reverse('importacao:processoview', kwargs={'pk': self.pk})

    def etapa(self, codigo):
        for etapa in self.etapas.all():
            if etapa.codigo == codigo:
                return etapa
        return None

    @property
    def etapa_atual(self):
        for etapa in self.etapas.all():
            if not etapa.concluida:
                return etapa
        return None

    @property
    def progresso(self):
        etapas = list(self.etapas.all())
        if not etapas:
            return 0
        return int(100 * sum(1 for e in etapas if e.concluida) / len(etapas))

    @property
    def data_chegada(self):
        chegada = self.etapa('chegada')
        if chegada:
            return chegada.data_realizada or chegada.data_prevista
        return None

    @property
    def prazo_devolucao(self):
        if self.modal != 'maritimo' or not self.data_chegada:
            return None
        return self.data_chegada + timedelta(days=self.free_time_dias)

    @property
    def valor_aduaneiro(self):
        return (self.valor_mercadoria + self.valor_frete + self.valor_seguro) * self.taxa_cambio

    @property
    def total_custos(self):
        return sum((custo.valor for custo in self.custos.all()), Decimal('0.00'))

    @property
    def demurrage_estimada(self):
        return sum((c.valor_demurrage for c in self.containers.all()), Decimal('0.00'))

    @property
    def custo_total(self):
        return self.valor_aduaneiro + self.total_custos

    def sincronizar(self):
        """Mantem a etapa de devolucao e o status coerentes com o modal e os containers."""
        devolucao = self.etapas.filter(codigo='devolucao').first()
        if devolucao:
            containers = list(self.containers.all())
            if self.modal != 'maritimo':
                devolucao.nao_aplica = True
                devolucao.data_realizada = None
            elif containers:
                datas = [c.data_devolucao for c in containers]
                devolucao.nao_aplica = False
                devolucao.data_realizada = max(datas) if all(datas) else None
            devolucao.save()

        if self.status != 'cancelado':
            pendentes = self.etapas.filter(
                nao_aplica=False, data_realizada__isnull=True).exists()
            status = 'andamento' if pendentes else 'concluido'
            if status != self.status:
                self.status = status
                ProcessoImportacao.objects.filter(
                    pk=self.pk).update(status=status)


class EtapaImportacao(models.Model):
    processo = models.ForeignKey(
        ProcessoImportacao, related_name='etapas', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, choices=ETAPAS)
    ordem = models.PositiveSmallIntegerField(default=0)
    data_prevista = models.DateField(null=True, blank=True)
    data_realizada = models.DateField(null=True, blank=True)
    nao_aplica = models.BooleanField(default=False)
    observacao = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Etapa da importação'
        ordering = ['ordem']
        unique_together = ('processo', 'codigo')

    def __str__(self):
        return self.get_codigo_display()

    @property
    def concluida(self):
        return self.nao_aplica or self.data_realizada is not None

    @property
    def atrasada(self):
        return not self.concluida and self.data_prevista is not None and self.data_prevista < date.today()


class ContainerImportacao(models.Model):
    processo = models.ForeignKey(
        ProcessoImportacao, related_name='containers', on_delete=models.CASCADE)
    numero = models.CharField(max_length=20)
    tipo = models.CharField(
        max_length=5, choices=TIPOS_CONTAINER, default='40hc')
    lacre = models.CharField(max_length=30, blank=True, default='')
    data_retirada = models.DateField(null=True, blank=True)
    data_devolucao = models.DateField(null=True, blank=True)
    local_devolucao = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        verbose_name = 'Container'
        ordering = ['id']

    def __str__(self):
        return self.numero

    @property
    def prazo_devolucao(self):
        return self.processo.prazo_devolucao

    @property
    def dias_demurrage(self):
        prazo = self.prazo_devolucao
        if not prazo:
            return 0
        return max(((self.data_devolucao or date.today()) - prazo).days, 0)

    @property
    def valor_demurrage(self):
        return self.dias_demurrage * self.processo.demurrage_diaria


class CustoImportacao(models.Model):
    processo = models.ForeignKey(
        ProcessoImportacao, related_name='custos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=12, choices=TIPOS_CUSTO)
    descricao = models.CharField(max_length=255, blank=True, default='')
    valor = models.DecimalField(
        max_digits=15, decimal_places=2, validators=VALOR_MINIMO)
    data_vencimento = models.DateField(null=True, blank=True)
    pago = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Custo da importação'
        ordering = ['id']

    def __str__(self):
        return self.get_tipo_display()


class DocumentoImportacao(models.Model):
    processo = models.ForeignKey(
        ProcessoImportacao, related_name='documentos', on_delete=models.CASCADE)
    tipo = models.CharField(
        max_length=12, choices=TIPOS_DOCUMENTO, default='outro')
    arquivo = models.FileField(
        upload_to='importacao/%Y/%m/', storage=DocumentosPrivadosStorage())
    nome = models.CharField(max_length=255)
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento da importação'
        ordering = ['id']

    def __str__(self):
        return self.nome


@receiver(post_delete, sender=DocumentoImportacao)
def remover_arquivo_documento(sender, instance, **kwargs):
    instance.arquivo.delete(save=False)
