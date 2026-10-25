# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from djangosige.apps.cadastro.models import Cliente, Empresa


# ==================== MÓDULO 1: ENTRADA DE CLIENTE ====================

class ProcessoContabil(models.Model):
    """Processo principal que integra todos os módulos"""
    
    STATUS_CHOICES = [
        ('entrada', 'Entrada de Cliente'),
        ('legalizacao', 'Legalização'),
        ('dp', 'Departamento Pessoal'),
        ('fiscal', 'Fiscal'),
        ('contabil', 'Contábil'),
        ('concluido', 'Concluído'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='processos_contabeis')
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True)
    numero_processo = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='entrada')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processos_responsavel')
    equipe = models.ManyToManyField(User, related_name='processos_equipe', blank=True)
    
    # Metadados
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    
    # Campos de controle
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Processo Contábil'
        verbose_name_plural = 'Processos Contábeis'
        ordering = ['-data_abertura']
    
    def __str__(self):
        return f"{self.numero_processo} - {self.cliente}"
    
    def get_etapa_atual(self):
        """Retorna o número da etapa atual (1-5)"""
        etapas = {
            'entrada': 1,
            'legalizacao': 2,
            'dp': 3,
            'fiscal': 4,
            'contabil': 5,
            'concluido': 5
        }
        return etapas.get(self.status, 1)
    
    def get_progresso(self):
        """Retorna o progresso em % (0-100)"""
        return (self.get_etapa_atual() / 5) * 100


class EntradaCliente(models.Model):
    """Módulo 1: Entrada de Cliente"""
    
    processo = models.OneToOneField(ProcessoContabil, on_delete=models.CASCADE, related_name='entrada')
    
    # Contato inicial
    data_contato_inicial = models.DateTimeField()
    canal_contato = models.CharField(max_length=50, choices=[
        ('telefone', 'Telefone'),
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('presencial', 'Presencial'),
        ('indicacao', 'Indicação'),
        ('site', 'Site'),
    ])
    
    # Coleta de informações
    informacoes_coletadas = models.TextField(help_text='Informações básicas do cliente e necessidades')
    documentos_recebidos = models.TextField(blank=True, help_text='Lista de documentos recebidos')
    
    # Análise da necessidade
    tipo_servico = models.CharField(max_length=100, choices=[
        ('abertura_empresa', 'Abertura de Empresa'),
        ('alteracao_empresa', 'Alteração de Empresa'),
        ('baixa_empresa', 'Baixa de Empresa'),
        ('contabilidade_completa', 'Contabilidade Completa'),
        ('dp_folha', 'DP e Folha de Pagamento'),
        ('consultoria_fiscal', 'Consultoria Fiscal'),
        ('outros', 'Outros'),
    ])
    necessidades_identificadas = models.TextField()
    
    # Escopo e equipe
    escopo_definido = models.TextField(help_text='Escopo detalhado dos serviços')
    proposta_valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proposta_aceita = models.BooleanField(default=False)
    data_aceite = models.DateTimeField(null=True, blank=True)
    
    # Status
    concluida = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Entrada de Cliente'
        verbose_name_plural = 'Entradas de Clientes'
    
    def __str__(self):
        return f"Entrada - {self.processo.numero_processo}"


# ==================== MÓDULO 2: LEGALIZAÇÃO ====================

class Legalizacao(models.Model):
    """Módulo 2: Legalização"""
    
    processo = models.OneToOneField(ProcessoContabil, on_delete=models.CASCADE, related_name='legalizacao')
    
    # Abertura/Alteração/Baixa
    tipo_operacao = models.CharField(max_length=20, choices=[
        ('abertura', 'Abertura'),
        ('alteracao', 'Alteração'),
        ('baixa', 'Baixa'),
    ])
    natureza_juridica = models.CharField(max_length=50, blank=True)
    
    # Junta Comercial (JUCEMG)
    data_protocolo_junta = models.DateField(null=True, blank=True)
    numero_protocolo_junta = models.CharField(max_length=50, blank=True)
    data_deferimento_junta = models.DateField(null=True, blank=True)
    numero_registro = models.CharField(max_length=50, blank=True, help_text='NIRE ou número de registro')
    
    # CNPJ
    cnpj = models.CharField(max_length=18, blank=True)
    data_emissao_cnpj = models.DateField(null=True, blank=True)
    
    # Inscrições municipais e estaduais
    inscricao_municipal = models.CharField(max_length=50, blank=True)
    data_inscricao_municipal = models.DateField(null=True, blank=True)
    inscricao_estadual = models.CharField(max_length=50, blank=True)
    data_inscricao_estadual = models.DateField(null=True, blank=True)
    
    # Alvarás e licenças
    alvara_funcionamento = models.CharField(max_length=50, blank=True)
    data_alvara = models.DateField(null=True, blank=True)
    licencas_especiais = models.TextField(blank=True, help_text='Licenças especiais necessárias')
    
    # Órgãos reguladores
    cadastro_orgaos_reguladores = models.TextField(blank=True, help_text='Ex: ANVISA, CRM, CREA, etc.')
    
    # Status
    regularizada = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Legalização'
        verbose_name_plural = 'Legalizações'
    
    def __str__(self):
        return f"Legalização - {self.processo.numero_processo}"


# ==================== MÓDULO 3: DEPARTAMENTO PESSOAL ====================

class DepartamentoPessoal(models.Model):
    """Módulo 3: Departamento Pessoal"""
    
    processo = models.OneToOneField(ProcessoContabil, on_delete=models.CASCADE, related_name='dp')
    
    # Configuração inicial
    regime_tributario_folha = models.CharField(max_length=50, choices=[
        ('simples', 'Simples Nacional'),
        ('lucro_presumido', 'Lucro Presumido'),
        ('lucro_real', 'Lucro Real'),
    ], default='simples')
    
    # Estatísticas
    total_funcionarios = models.IntegerField(default=0)
    total_admissoes_mes = models.IntegerField(default=0)
    total_demissoes_mes = models.IntegerField(default=0)
    
    # eSocial
    esocial_ativo = models.BooleanField(default=False)
    data_implantacao_esocial = models.DateField(null=True, blank=True)
    
    # Status
    em_dia = models.BooleanField(default=True)
    ultima_folha_processada = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Departamento Pessoal'
        verbose_name_plural = 'Departamentos Pessoais'
    
    def __str__(self):
        return f"DP - {self.processo.numero_processo}"


class Funcionario(models.Model):
    """Cadastro de funcionários"""
    
    dp = models.ForeignKey(DepartamentoPessoal, on_delete=models.CASCADE, related_name='funcionarios')
    
    # Dados pessoais
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    
    # Admissão
    data_admissao = models.DateField()
    cargo = models.CharField(max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Demissão
    ativo = models.BooleanField(default=True)
    data_demissao = models.DateField(null=True, blank=True)
    motivo_demissao = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome_completo']
    
    def __str__(self):
        return self.nome_completo


class FolhaPagamento(models.Model):
    """Folhas de pagamento mensais"""
    
    dp = models.ForeignKey(DepartamentoPessoal, on_delete=models.CASCADE, related_name='folhas')
    
    mes_referencia = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    ano_referencia = models.IntegerField()
    
    data_processamento = models.DateTimeField(auto_now_add=True)
    total_proventos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_descontos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_liquido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Encargos
    inss_empresa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fgts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    processada = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Folha de Pagamento'
        verbose_name_plural = 'Folhas de Pagamento'
        ordering = ['-ano_referencia', '-mes_referencia']
        unique_together = ['dp', 'mes_referencia', 'ano_referencia']
    
    def __str__(self):
        return f"Folha {self.mes_referencia:02d}/{self.ano_referencia} - {self.dp.processo.numero_processo}"


# ==================== MÓDULO 4: FISCAL ====================

class Fiscal(models.Model):
    """Módulo 4: Fiscal"""
    
    processo = models.OneToOneField(ProcessoContabil, on_delete=models.CASCADE, related_name='fiscal')
    
    # Regime fiscal
    regime_tributario = models.CharField(max_length=50, choices=[
        ('simples', 'Simples Nacional'),
        ('lucro_presumido', 'Lucro Presumido'),
        ('lucro_real', 'Lucro Real'),
        ('mei', 'MEI'),
    ])
    anexo_simples = models.CharField(max_length=10, blank=True, help_text='Ex: Anexo I, II, III, IV, V')
    
    # Estatísticas do mês
    total_nf_emitidas = models.IntegerField(default=0)
    total_nf_recebidas = models.IntegerField(default=0)
    faturamento_mes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Tributos apurados
    ultima_apuracao = models.DateField(null=True, blank=True)
    
    # Obrigações acessórias
    sped_fiscal = models.BooleanField(default=False)
    sped_contribuicoes = models.BooleanField(default=False)
    sped_ecd = models.BooleanField(default=False)
    
    # Status
    em_dia = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Fiscal'
        verbose_name_plural = 'Fiscais'
    
    def __str__(self):
        return f"Fiscal - {self.processo.numero_processo}"


class ApuracaoTributos(models.Model):
    """Apuração mensal de tributos"""
    
    fiscal = models.ForeignKey(Fiscal, on_delete=models.CASCADE, related_name='apuracoes')
    
    mes_referencia = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    ano_referencia = models.IntegerField()
    
    # Valores
    receita_bruta = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Tributos federais
    irpj = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    csll = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cofins = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    simples_nacional = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tributos estaduais
    icms = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tributos municipais
    iss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    total_tributos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status
    data_apuracao = models.DateTimeField(auto_now_add=True)
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Apuração de Tributos'
        verbose_name_plural = 'Apurações de Tributos'
        ordering = ['-ano_referencia', '-mes_referencia']
        unique_together = ['fiscal', 'mes_referencia', 'ano_referencia']
    
    def __str__(self):
        return f"Apuração {self.mes_referencia:02d}/{self.ano_referencia} - {self.fiscal.processo.numero_processo}"


class ObrigacaoAcessoria(models.Model):
    """Controle de obrigações acessórias (SPED, DAPI, etc.)"""
    
    fiscal = models.ForeignKey(Fiscal, on_delete=models.CASCADE, related_name='obrigacoes')
    
    tipo = models.CharField(max_length=50, choices=[
        ('sped_fiscal', 'SPED Fiscal'),
        ('sped_contribuicoes', 'SPED Contribuições'),
        ('sped_ecd', 'SPED ECD'),
        ('dctf', 'DCTF'),
        ('dapi', 'DAPI'),
        ('defis', 'DEFIS'),
        ('gfip', 'GFIP'),
        ('dirf', 'DIRF'),
        ('outros', 'Outros'),
    ])
    
    mes_referencia = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    ano_referencia = models.IntegerField()
    
    data_vencimento = models.DateField()
    entregue = models.BooleanField(default=False)
    data_entrega = models.DateTimeField(null=True, blank=True)
    numero_recibo = models.CharField(max_length=100, blank=True)
    
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Obrigação Acessória'
        verbose_name_plural = 'Obrigações Acessórias'
        ordering = ['data_vencimento']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.mes_referencia:02d}/{self.ano_referencia}"


# ==================== MÓDULO 5: CONTÁBIL ====================

class Contabil(models.Model):
    """Módulo 5: Contábil"""
    
    processo = models.OneToOneField(ProcessoContabil, on_delete=models.CASCADE, related_name='contabil')
    
    # Plano de contas
    plano_contas_implantado = models.BooleanField(default=False)
    data_implantacao_plano = models.DateField(null=True, blank=True)
    
    # Conciliação bancária
    ultima_conciliacao = models.DateField(null=True, blank=True)
    contas_bancarias_cadastradas = models.IntegerField(default=0)
    
    # Demonstrações
    ultima_dre = models.DateField(null=True, blank=True)
    ultimo_balancete = models.DateField(null=True, blank=True)
    ultimo_balanco = models.DateField(null=True, blank=True)
    
    # Status
    em_dia = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Contábil'
        verbose_name_plural = 'Contábeis'
    
    def __str__(self):
        return f"Contábil - {self.processo.numero_processo}"


class LancamentoContabil(models.Model):
    """Lançamentos contábeis"""
    
    contabil = models.ForeignKey(Contabil, on_delete=models.CASCADE, related_name='lancamentos')
    
    data_lancamento = models.DateField()
    numero_lancamento = models.CharField(max_length=20)
    
    tipo = models.CharField(max_length=20, choices=[
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ])
    
    # Contas
    conta_debito = models.CharField(max_length=50)
    conta_credito = models.CharField(max_length=50)
    
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    historico = models.TextField()
    
    # Documento origem
    documento_tipo = models.CharField(max_length=50, blank=True)
    documento_numero = models.CharField(max_length=50, blank=True)
    
    # Controle
    data_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Lançamento Contábil'
        verbose_name_plural = 'Lançamentos Contábeis'
        ordering = ['-data_lancamento', '-numero_lancamento']
    
    def __str__(self):
        return f"{self.numero_lancamento} - {self.data_lancamento}"


class ConciliacaoBancaria(models.Model):
    """Conciliações bancárias mensais"""
    
    contabil = models.ForeignKey(Contabil, on_delete=models.CASCADE, related_name='conciliacoes')
    
    mes_referencia = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    ano_referencia = models.IntegerField()
    
    banco = models.CharField(max_length=100)
    agencia = models.CharField(max_length=20)
    conta = models.CharField(max_length=20)
    
    saldo_inicial = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_final = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_extrato = models.DecimalField(max_digits=15, decimal_places=2)
    
    conciliada = models.BooleanField(default=False)
    data_conciliacao = models.DateTimeField(null=True, blank=True)
    
    divergencias = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Conciliação Bancária'
        verbose_name_plural = 'Conciliações Bancárias'
        ordering = ['-ano_referencia', '-mes_referencia']
    
    def __str__(self):
        return f"Conciliação {self.banco} - {self.mes_referencia:02d}/{self.ano_referencia}"


class DemonstracaoResultado(models.Model):
    """DRE - Demonstração do Resultado do Exercício"""
    
    contabil = models.ForeignKey(Contabil, on_delete=models.CASCADE, related_name='dres')
    
    mes_referencia = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    ano_referencia = models.IntegerField()
    
    # Receitas
    receita_bruta = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deducoes_receita = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    receita_liquida = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Custos e despesas
    cmv = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Custo da Mercadoria Vendida')
    lucro_bruto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    despesas_operacionais = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    despesas_administrativas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    despesas_financeiras = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    receitas_financeiras = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Resultado
    resultado_antes_ir = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    provisao_ir_csll = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    lucro_liquido = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Controle
    data_geracao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'DRE'
        verbose_name_plural = 'DREs'
        ordering = ['-ano_referencia', '-mes_referencia']
        unique_together = ['contabil', 'mes_referencia', 'ano_referencia']
    
    def __str__(self):
        return f"DRE {self.mes_referencia:02d}/{self.ano_referencia} - {self.contabil.processo.numero_processo}"
