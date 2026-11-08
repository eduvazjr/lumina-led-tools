from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from djangosige.apps.cadastro.models import Empresa
from djangosige.apps.financeiro_grupo.models import TransferenciaGrupo
from djangosige.apps.juridico.models import Processo


class FormulariosGestaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('gestao_forms', 'g@f.com', 'senha-teste')
        self.client.force_login(self.user)
        self.a = Empresa.objects.create(nome_razao_social='Empresa A Ltda', tipo_pessoa='PJ')
        self.b = Empresa.objects.create(nome_razao_social='Empresa B Ltda', tipo_pessoa='PJ')

    def test_nova_transferencia_aceita_valor_brasileiro_e_entra_pendente(self):
        r = self.client.post(reverse('financeiro_grupo:transferencia_add'), {
            'empresa_origem': self.a.pk, 'empresa_destino': self.b.pk, 'valor': '1.234.567,89',
            'tipo': 'emprestimo', 'data': '2026-11-08T10:30', 'finalidade': 'Capital de giro', 'observacoes': ''})
        t = TransferenciaGrupo.objects.get()
        self.assertRedirects(r, reverse('financeiro_grupo:transferencia_detail', args=[t.pk]))
        self.assertEqual(t.valor, Decimal('1234567.89'))
        self.assertEqual(t.status, 'pendente')
        self.assertEqual(t.usuario, self.user)
        self.assertContains(self.client.get(reverse('financeiro_grupo:transferencia_edit', args=[t.pk])), 'value="1.234.567,89"')

    def test_transferencia_para_a_mesma_empresa_e_recusada(self):
        r = self.client.post(reverse('financeiro_grupo:transferencia_add'), {
            'empresa_origem': self.a.pk, 'empresa_destino': self.a.pk, 'valor': '10,00',
            'tipo': 'outro', 'data': '2026-11-08T10:30', 'finalidade': 'x'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'precisa ser diferente')
        self.assertFalse(TransferenciaGrupo.objects.exists())

    def test_relatorio_de_transferencias_soma_por_situacao(self):
        for valor, status in [('100.00', 'concluida'), ('50.50', 'pendente')]:
            TransferenciaGrupo.objects.create(empresa_origem=self.a, empresa_destino=self.b, valor=Decimal(valor),
                                              status=status, data=timezone.now(), finalidade='x', usuario=self.user)
        r = self.client.get(reverse('financeiro_grupo:relatorio'))
        self.assertEqual(r.context['totais']['concluida'], Decimal('100.00'))
        self.assertEqual(r.context['totais']['pendente'], Decimal('50.50'))

    def test_nova_demanda_e_edicao(self):
        dados = {'numero': '0001-11.2026', 'empresa': self.a.pk, 'parte_contraria': 'Fulano', 'orgao': 'tjmg',
                 'tipo_processo': 'Trabalhista', 'descricao': 'Reclamação', 'valor_causa': '200.000,00',
                 'nivel_risco': 'alto', 'probabilidade_perda': '40', 'status': 'ativo',
                 'data_distribuicao': '2026-01-10', 'proximo_prazo': '', 'descricao_prazo': '',
                 'ultima_movimentacao': '', 'advogado_responsavel': '', 'observacoes': ''}
        r = self.client.post(reverse('juridico:processo_add'), dados)
        p = Processo.objects.get()
        self.assertRedirects(r, reverse('juridico:processo_detail', args=[p.pk]))
        self.assertEqual(p.valor_causa, Decimal('200000.00'))
        dados['probabilidade_perda'] = '150'
        r = self.client.post(reverse('juridico:processo_edit', args=[p.pk]), dados)
        self.assertContains(r, 'entre 0 e 100')
        detalhe = self.client.get(reverse('juridico:processo_detail', args=[p.pk]))
        self.assertContains(detalhe, 'TJMG - Tribunal de Justiça MG')
        relatorio = self.client.get(reverse('juridico:relatorio_risco'))
        self.assertEqual(relatorio.context['total_risco'], 80000.0)
        self.assertContains(relatorio, 'R$ 80.000,00')
