from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase

from djangosige.apps.base.templatetags.led_ui import brl, valor_brl


class ValorBrlTests(SimpleTestCase):
    def test_separa_moeda_inteiro_e_centavos_no_padrao_brasileiro(self):
        html = valor_brl(Decimal('195947762.79'))
        self.assertIn('<span class="valor-moeda">R$</span>', html)
        self.assertIn('<span class="valor-inteiro">195.947.762</span>', html)
        self.assertIn('<span class="valor-centavos">,79</span>', html)

    def test_zero_e_vazio_viram_zero_reais(self):
        self.assertIn('<span class="valor-inteiro">0</span><span class="valor-centavos">,00</span>', valor_brl(None))
        self.assertIn('<span class="valor-inteiro">0</span><span class="valor-centavos">,00</span>', valor_brl('0.00'))

    def test_negativo_e_tamanho(self):
        html = valor_brl('-1234.5', 'sm')
        self.assertIn('class="valor valor-sm"', html)
        self.assertIn('-R$', html)
        self.assertIn('>1.234<', html)

    def test_filtro_brl(self):
        self.assertEqual(brl('1234.56'), 'R$ 1.234,56')
        self.assertEqual(brl(0), 'R$ 0,00')
        self.assertEqual(brl('-10'), '-R$ 10,00')

    def test_tag_no_template(self):
        saida = Template('{% load led_ui %}{% valor_brl v %}|{{ v|brl }}').render(Context({'v': 1000}))
        self.assertIn('>1.000<', saida)
        self.assertIn('R$ 1.000,00', saida)
