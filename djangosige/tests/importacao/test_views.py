# -*- coding: utf-8 -*-

import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from djangosige.apps.base import agente
from djangosige.apps.importacao.models import ETAPAS, ProcessoImportacao
from djangosige.tests.test_case import BaseTestCase

MEDIA_TESTE = tempfile.mkdtemp()


def criar_processo(**extra):
    dados = dict(numero_ordem_compra='OC-1', exportador='Shenzhen Ltd', pais_origem='China',
                 mercadoria='Luminárias LED', valor_mercadoria=Decimal('1000.00'),
                 valor_frete=Decimal('200.00'), valor_seguro=Decimal('50.00'),
                 taxa_cambio=Decimal('5.0000'), free_time_dias=7, demurrage_diaria=Decimal('100.00'))
    dados.update(extra)
    return ProcessoImportacao.objects.create(**dados)


def dados_formset(prefixo, total=1, iniciais=0, **campos):
    dados = {'secao': prefixo, prefixo + '-TOTAL_FORMS': total, prefixo + '-INITIAL_FORMS': iniciais,
             prefixo + '-MIN_NUM_FORMS': 0, prefixo + '-MAX_NUM_FORMS': 1000}
    for campo, valor in campos.items():
        dados['%s-0-%s' % (prefixo, campo)] = valor
    return dados


@override_settings(DOCUMENTOS_PRIVADOS_ROOT=MEDIA_TESTE)
class ProcessoImportacaoTestCase(BaseTestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TESTE, ignore_errors=True)

    def url(self, processo):
        return reverse('importacao:processoview', kwargs={'pk': processo.pk})

    def concluir_etapas(self, processo, exceto=()):
        processo.etapas.exclude(codigo__in=exceto).update(data_realizada=date.today())

    def test_criar_processo_gera_referencia_e_todas_as_etapas(self):
        response = self.client.post(reverse('importacao:addprocessoview'), {
            'numero_ordem_compra': 'OC-77', 'exportador': 'Acme', 'pais_origem': 'China',
            'mercadoria': 'Fitas LED', 'modal': 'maritimo', 'incoterm': 'FOB', 'moeda': 'USD',
            'taxa_cambio': '5,4321', 'valor_mercadoria': '12.500,50', 'valor_frete': '0,00',
            'valor_seguro': '0,00', 'free_time_dias': '10', 'demurrage_diaria': '0,00'})
        processo = ProcessoImportacao.objects.get(numero_ordem_compra='OC-77')
        self.assertRedirects(response, self.url(processo))
        self.assertEqual(processo.referencia, 'IMP-%d-%04d' % (date.today().year, processo.pk))
        self.assertEqual(processo.valor_mercadoria, Decimal('12500.50'))
        self.assertEqual(processo.taxa_cambio, Decimal('5.4321'))
        self.assertEqual([e.codigo for e in processo.etapas.all()], [c for c, _ in ETAPAS])
        self.assertEqual(processo.etapa_atual.codigo, 'ordem_compra')

    def test_telas_abrem(self):
        processo = criar_processo()
        for url in (reverse('importacao:listaprocessosview'), reverse('importacao:addprocessoview'),
                    self.url(processo), reverse('importacao:editarprocessoview', kwargs={'pk': processo.pk})):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_lista_filtra_por_status(self):
        andamento = criar_processo()
        cancelado = criar_processo(status='cancelado')
        lista = reverse('importacao:listaprocessosview')
        self.assertEqual(list(self.client.get(lista).context['processos']), [andamento])
        self.assertEqual(list(self.client.get(lista, {'status': 'cancelado'}).context['processos']), [cancelado])

    def test_salvar_etapa(self):
        processo = criar_processo()
        etapas = list(processo.etapas.all())
        dados = {'secao': 'etapas', 'etapas-TOTAL_FORMS': len(etapas), 'etapas-INITIAL_FORMS': len(etapas),
                 'etapas-MIN_NUM_FORMS': 0, 'etapas-MAX_NUM_FORMS': 1000}
        for i, etapa in enumerate(etapas):
            dados['etapas-%d-id' % i] = etapa.pk
        dados['etapas-0-data_realizada'] = '10/03/2026'
        dados['etapas-1-nao_aplica'] = 'on'
        dados['etapas-2-data_prevista'] = '15/03/2026'
        self.client.post(self.url(processo), dados)
        etapas = list(processo.etapas.all())
        self.assertEqual(etapas[0].data_realizada, date(2026, 3, 10))
        self.assertTrue(etapas[1].nao_aplica)
        self.assertEqual(etapas[2].data_prevista, date(2026, 3, 15))
        self.assertEqual(processo.etapa_atual.codigo, 'cambio')

    def test_devolucao_de_todos_os_containers_conclui_o_processo(self):
        processo = criar_processo()
        self.concluir_etapas(processo, exceto=['devolucao'])
        self.client.post(self.url(processo), dados_formset(
            'containers', numero='MSCU1234567', tipo='40hc'))
        container = processo.containers.get()
        processo.refresh_from_db()
        self.assertEqual(processo.status, 'andamento')

        dados = dados_formset('containers', iniciais=1, id=container.pk, numero='MSCU1234567',
                              tipo='40hc', data_devolucao='20/03/2026')
        self.client.post(self.url(processo), dados)
        processo = ProcessoImportacao.objects.get(pk=processo.pk)
        self.assertEqual(processo.etapas.get(codigo='devolucao').data_realizada, date(2026, 3, 20))
        self.assertEqual(processo.status, 'concluido')

    def test_modal_aereo_nao_tem_devolucao_de_container(self):
        processo = criar_processo(modal='aereo')
        self.assertTrue(processo.etapas.get(codigo='devolucao').nao_aplica)
        self.assertNotContains(self.client.get(self.url(processo)), 'Salvar containers')

    def test_demurrage_conta_dias_apos_o_free_time(self):
        processo = criar_processo()
        processo.etapas.filter(codigo='chegada').update(data_realizada=date.today() - timedelta(days=10))
        container = processo.containers.create(numero='C1')
        self.assertEqual(container.dias_demurrage, 3)
        self.assertEqual(container.valor_demurrage, Decimal('300.00'))

    def test_custos_compoem_o_custo_total(self):
        processo = criar_processo()
        self.client.post(self.url(processo), dados_formset('custos', tipo='ii', valor='1.000,50'))
        processo = ProcessoImportacao.objects.get(pk=processo.pk)
        self.assertEqual(processo.total_custos, Decimal('1000.50'))
        self.assertEqual(processo.valor_aduaneiro, Decimal('6250.00'))
        self.assertEqual(processo.custo_total, Decimal('7250.50'))

    def test_documentos_enviar_abrir_remover(self):
        processo = criar_processo()
        self.client.post(self.url(processo), {
            'secao': 'documentos', 'tipo': 'invoice',
            'arquivos': [SimpleUploadedFile('invoice.pdf', b'%PDF a'), SimpleUploadedFile('bl.png', b'png')]})
        self.assertEqual(processo.documentos.count(), 2)
        documento = processo.documentos.get(nome='invoice.pdf')
        url = reverse('importacao:documentoview', kwargs={'pk': documento.pk})
        self.assertEqual(b''.join(self.client.get(url).streaming_content), b'%PDF a')

        self.client.post(self.url(processo), {'secao': 'documentos', 'remover': documento.pk})
        self.assertEqual(processo.documentos.count(), 1)

    def test_documento_recusa_extensao_nao_permitida(self):
        processo = criar_processo()
        response = self.client.post(self.url(processo), {
            'secao': 'documentos', 'tipo': 'outro', 'arquivos': [SimpleUploadedFile('x.html', b'<script>')]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(processo.documentos.count(), 0)

    def test_permissoes(self):
        processo = criar_processo()
        self.check_user_get_permission(
            reverse('importacao:listaprocessosview'), permission_codename='view_processoimportacao')
        self.check_user_get_permission(
            reverse('importacao:addprocessoview'), permission_codename='add_processoimportacao')
        self.check_user_get_permission(self.url(processo), permission_codename='view_processoimportacao')

    def test_alertas_de_prazos(self):
        hoje = date.today()
        processo = criar_processo(numero_ordem_compra='OC-A')
        processo.etapas.filter(codigo='chegada').update(data_realizada=hoje - timedelta(days=9))
        processo.containers.create(numero='C1')
        processo.etapas.filter(codigo='registro').update(data_prevista=hoje - timedelta(days=1))
        processo.custos.create(tipo='ii', valor=Decimal('10.00'), data_vencimento=hoje)

        navio = criar_processo(numero_ordem_compra='OC-B')
        navio.etapas.filter(codigo='chegada').update(data_prevista=hoje + timedelta(days=2))

        titulos = ' | '.join(a.titulo for a in agente.regras_importacao(hoje))
        self.assertIn('Demurrage', titulos)
        self.assertIn('atrasada', titulos)
        self.assertIn('Custo', titulos)
        self.assertIn('Chegada prevista', titulos)

        pronto = criar_processo(status='cancelado')
        pronto.containers.create(numero='C2')
        self.assertNotIn(pronto.referencia, ' '.join(a.detalhe for a in agente.regras_importacao(hoje)))
