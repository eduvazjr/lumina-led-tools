from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from djangosige.apps.base import agente
from djangosige.apps.cadastro.models import Empresa
from djangosige.apps.contabilidade.models import ApuracaoTributos, Funcionario, ObrigacaoAcessoria, ProcessoContabil


class ContabilidadePorEmpresaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('contab_emp', 'c@e.com', 'senha-teste')
        self.client.force_login(self.user)
        self.empresa = Empresa.objects.create(nome_razao_social='Led Tools Importadora Ltda', tipo_pessoa='PJ')

    def test_painel_lista_as_empresas_do_grupo(self):
        r = self.client.get(reverse('contabilidade:dashboard'))
        self.assertContains(r, 'Led Tools Importadora Ltda')
        self.assertContains(r, 'Contabilidade ainda não iniciada')
        self.assertNotContains(r, 'Entrada de cliente')

    def test_fluxo_completo_da_empresa(self):
        url_empresa = reverse('contabilidade:empresa', args=[self.empresa.pk])
        self.assertContains(self.client.get(url_empresa), 'Preencher dados fiscais')
        self.assertEqual(ProcessoContabil.objects.get().empresa, self.empresa)
        # Sem dados fiscais, a apuração leva primeiro aos dados fiscais
        r = self.client.get(reverse('contabilidade:novo_registro', args=[self.empresa.pk, 'apuracao']))
        self.assertRedirects(r, reverse('contabilidade:dados_empresa', args=[self.empresa.pk, 'fiscal']))
        r = self.client.post(reverse('contabilidade:dados_empresa', args=[self.empresa.pk, 'fiscal']),
                             {'regime_tributario': 'lucro_real', 'em_dia': 'on'})
        self.assertRedirects(r, url_empresa + '#fiscal', fetch_redirect_response=False)
        hoje = date.today()
        r = self.client.post(reverse('contabilidade:novo_registro', args=[self.empresa.pk, 'apuracao']), {
            'mes_referencia': 1, 'ano_referencia': hoje.year - 1, 'receita_bruta': '150.000,00',
            'irpj': '0', 'csll': '0', 'pis': '0', 'cofins': '0', 'simples_nacional': '0', 'icms': '0', 'iss': '0',
            'total_tributos': '12.345,67'})
        self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
        apuracao = ApuracaoTributos.objects.get()
        self.assertEqual(apuracao.total_tributos, Decimal('12345.67'))
        r = self.client.post(reverse('contabilidade:novo_registro', args=[self.empresa.pk, 'funcionario']), {
            'nome_completo': 'Ana Souza', 'cpf': '123.456.789-00', 'data_nascimento': '1990-05-01',
            'data_admissao': '2024-02-01', 'cargo': 'Analista fiscal', 'salario': '4.500,00', 'ativo': 'on'})
        self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
        pagina = self.client.get(url_empresa)
        self.assertContains(pagina, 'R$ 12.345,67')
        self.assertContains(pagina, 'Ana Souza')
        self.assertContains(pagina, 'R$ 4.500,00')
        # Remover
        func = Funcionario.objects.get()
        self.client.post(reverse('contabilidade:remover_registro', args=[self.empresa.pk, 'funcionario', func.pk]))
        self.assertFalse(Funcionario.objects.exists())

    def test_alertas_citam_a_empresa(self):
        self.client.get(reverse('contabilidade:empresa', args=[self.empresa.pk]))
        self.client.post(reverse('contabilidade:dados_empresa', args=[self.empresa.pk, 'fiscal']), {'regime_tributario': 'lucro_real', 'em_dia': 'on'})
        fiscal = ProcessoContabil.objects.get().fiscal
        ObrigacaoAcessoria.objects.create(fiscal=fiscal, tipo='dctf', mes_referencia=1, ano_referencia=2026,
                                          data_vencimento=date.today() + timedelta(days=1))
        alerta = next(a for a in agente.regras_contabilidade(date.today()) if 'não entregue' in a.titulo)
        self.assertIn('Led Tools Importadora Ltda', alerta.detalhe)
        self.assertIn(reverse('contabilidade:empresa', args=[self.empresa.pk]), alerta.url)
