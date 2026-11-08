from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from djangosige.apps.cadastro.models import Empresa, PessoaJuridica
from djangosige.apps.financeiro_grupo.models import TransferenciaGrupo


class FinanceiroGrupoDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('grupo_tester', 'g@t.com', 'senha-de-teste')
        self.client.force_login(self.user)
        self.a = Empresa.objects.create(nome_razao_social='Led Tools Importadora Ltda', tipo_pessoa='PJ')
        PessoaJuridica.objects.create(pessoa_id=self.a, nome_fantasia='Led Importadora')
        self.b = Empresa.objects.create(nome_razao_social='Lumina Comercio Ltda', tipo_pessoa='PJ')

    def test_abre_com_empresas_cadastradas_e_mostra_nomes(self):
        TransferenciaGrupo.objects.create(
            empresa_origem=self.a, empresa_destino=self.b, valor=Decimal('1234.56'),
            status='concluida', data=timezone.now(), finalidade='Capital de giro', usuario=self.user)
        response = self.client.get(reverse('financeiro_grupo:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Led Importadora')       # nome fantasia
        self.assertContains(response, 'Lumina Comercio Ltda')  # sem nome fantasia: razão social
        self.assertContains(response, 'R$ 1.234,56')
