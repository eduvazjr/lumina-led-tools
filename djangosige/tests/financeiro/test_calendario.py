# -*- coding: utf-8 -*-

from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import openpyxl
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import PatternFill

from djangosige.apps.base import agente
from djangosige.apps.financeiro.models import ItemCalendario, ProgramacaoMes, Saida
from djangosige.apps.financeiro.planilha_calendario import importar_planilha, interpretar_item
from djangosige.tests.test_case import BaseTestCase

CINZA = PatternFill('solid', fgColor='FFB7B7B7')


def planilha_de_teste():
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.title = 'NOVEMBRO 2026'
    aba['C1'] = 'CONTAS A PAGAR\nNOVEMBRO 2026'
    for coluna, nome in enumerate(('DOMINGO ', 'SEGUNDA ', 'TERÇA ', 'QUARTA ', 'QUINTA ', 'SEXTA ', 'SÁBADO ', 'PROGRAMAÇÃO'), start=2):
        aba.cell(row=2, column=coluna, value=nome)
    aba['I3'] = '- Férias Ana 10/12 a 20/12'
    # Novembro/2026 comeca no domingo: C3 e segunda, dia 2
    aba['B3'] = 1
    aba['C3'] = '2\n- Boleto Fox NF 6296 R$ 6.922,50 OK\n- Terra R$ 100,00 / R$ 200,00\n- Base\nR$ 35.951,27'
    aba['D3'] = '3\n- Dia fechado R$ 10,00'
    aba['D3'].fill = CINZA
    aba['E3'] = CellRichText('4\n', TextBlock(InlineFont(color='FFFF0000'), '- Folha de Pagamento R$ '), '\n- Copasa R$ 33,94')
    aba['F3'] = '5- \n-Lion NF 64 R$ 1.000'
    aba['C7'] = '30\n- Parcelamento ISS R$ 201,68'
    # Dia repetido na aba seguinte nao pode duplicar
    outra = livro.create_sheet('DEZEMBRO 2026')
    outra['C1'] = 'CONTAS A PAGAR\nDEZEMBRO 2026'
    for coluna, nome in enumerate(('DOMINGO ', 'SEGUNDA ', 'TERÇA ', 'QUARTA ', 'QUINTA ', 'SEXTA ', 'SÁBADO '), start=2):
        outra.cell(row=2, column=coluna, value=nome)
    outra['C3'] = '30\n- Parcelamento ISS R$ 201,68'
    livro.create_sheet('Folha5')
    saida = BytesIO()
    livro.save(saida)
    return saida.getvalue()


class InterpretarItemTestCase(BaseTestCase):

    def test_interpreta_linhas_reais(self):
        self.assertEqual(interpretar_item('Boleto Terra NF 23962 R$ 67151,79'),
                         ('Boleto Terra NF 23962', [Decimal('67151.79')], False))
        self.assertEqual(interpretar_item('Padaria da Silva R$ 1.753,42 NF 3585'),
                         ('Padaria da Silva NF 3585', [Decimal('1753.42')], False))
        self.assertEqual(interpretar_item('Fornecedor Kiki R$ 10.000'),
                         ('Fornecedor Kiki', [Decimal('10000.00')], False))
        self.assertEqual(interpretar_item('Copasa L&T Identificador 16880085-3 R$ '),
                         ('Copasa L&T Identificador 16880085-3', [None], False))
        self.assertEqual(interpretar_item('Boletos R$ 141,31 / R$ 182,56 ok')[1:],
                         ([Decimal('141.31'), Decimal('182.56')], True))
        # "ok" dentro de outra palavra nao conclui
        self.assertFalse(interpretar_item('Book fiscal')[2])


class CalendarioTestCase(BaseTestCase):
    url = reverse('financeiro:calendarioview')

    def importar(self):
        arquivo = SimpleUploadedFile('Calendario.xlsx', planilha_de_teste())
        return self.client.post(reverse('financeiro:importarcalendarioview'), {'arquivo': arquivo}, follow=True)

    def test_importa_planilha(self):
        self.assertContains(self.importar(), 'Importação concluída')

        fox = ItemCalendario.objects.get(descricao='Boleto Fox NF 6296')
        self.assertEqual(fox.data, date(2026, 11, 2))
        self.assertEqual(fox.valor, Decimal('6922.50'))
        self.assertTrue(fox.concluido)

        terra = ItemCalendario.objects.filter(descricao='Terra', data=date(2026, 11, 2))
        self.assertEqual(sorted(i.valor for i in terra), [Decimal('100.00'), Decimal('200.00')])
        # Valor na linha seguinte pertence ao item anterior
        self.assertEqual(ItemCalendario.objects.get(descricao='Base').valor, Decimal('35951.27'))
        # Celula cinza em dia util conta como concluida
        self.assertTrue(ItemCalendario.objects.get(descricao='Dia fechado').concluido)

        folha = ItemCalendario.objects.get(descricao='Folha de Pagamento')
        self.assertIsNone(folha.valor)
        self.assertTrue(folha.destaque)
        self.assertFalse(ItemCalendario.objects.get(descricao='Copasa').destaque)
        self.assertEqual(ItemCalendario.objects.get(descricao='Lion NF 64').data, date(2026, 11, 5))

        self.assertEqual(ProgramacaoMes.objects.get(ano=2026, mes=11).texto, '- Férias Ana 10/12 a 20/12')
        # 30/11 aparece nas duas abas e so entra uma vez
        self.assertEqual(ItemCalendario.objects.filter(descricao='Parcelamento ISS', data=date(2026, 11, 30)).count(), 1)

    def test_aba_sem_a_primeira_semana_usa_o_dia_escrito(self):
        livro = openpyxl.Workbook()
        aba = livro.active
        aba.title = 'MARÇO 2025'
        aba['C1'] = 'CONTAS A PAGAR\nMARÇO 2025'
        aba['B2'] = 'DOMINGO '
        # 1/3/2025 e sabado e a planilha comeca em 2/3; 24 tambem existe em fevereiro na segunda
        aba['C3'] = '3\n- Aluguel'
        aba['C6'] = '24\n- Starlink'
        arquivo = BytesIO()
        livro.save(arquivo)
        arquivo.seek(0)
        importar_planilha(arquivo)
        self.assertEqual(ItemCalendario.objects.get(descricao='Aluguel').data, date(2025, 3, 3))
        self.assertEqual(ItemCalendario.objects.get(descricao='Starlink').data, date(2025, 3, 24))

    def test_reimportar_nao_duplica_nem_desfaz_baixa(self):
        self.importar()
        total = ItemCalendario.objects.count()
        copasa = ItemCalendario.objects.get(descricao='Copasa')
        copasa.concluido = True
        copasa.save()
        self.importar()
        self.assertEqual(ItemCalendario.objects.count(), total)
        copasa.refresh_from_db()
        self.assertTrue(copasa.concluido)

    def test_arquivo_invalido_nao_quebra(self):
        response = self.client.post(reverse('financeiro:importarcalendarioview'),
                                    {'arquivo': SimpleUploadedFile('x.xlsx', b'nao e excel')})
        self.assertContains(response, 'Não foi possível ler')
        response = self.client.post(reverse('financeiro:importarcalendarioview'),
                                    {'arquivo': SimpleUploadedFile('x.pdf', b'x')})
        self.assertContains(response, 'Envie um arquivo .xlsx')

    def test_tela_mostra_mes_totais_e_contas(self):
        ItemCalendario.objects.create(data=date(2026, 11, 10), descricao='Aluguel', valor=Decimal('100.00'), concluido=True)
        ItemCalendario.objects.create(data=date(2026, 11, 10), descricao='Luz', valor=Decimal('50.00'))
        ItemCalendario.objects.create(data=date(2026, 12, 10), descricao='Outro mes', valor=Decimal('9.00'))
        Saida.objects.create(descricao='Conta lancada', status='1', data_vencimento=date(2026, 11, 10), valor_liquido=Decimal('5.00'))

        response = self.client.get(self.url, {'ano': 2026, 'mes': 11})
        self.assertEqual(response.context['resumo']['total'], Decimal('150.00'))
        self.assertEqual(response.context['resumo']['total_concluido'], Decimal('100.00'))
        self.assertEqual(response.context['resumo']['total_pendente'], Decimal('50.00'))
        self.assertContains(response, 'Novembro 2026')
        self.assertContains(response, 'Conta lancada')
        self.assertNotContains(response, 'Outro mes')

    def test_parametros_invalidos_voltam_para_o_mes_atual(self):
        for parametros in ({'ano': 'x', 'mes': '1'}, {'ano': 2026, 'mes': 13}):
            self.assertEqual(self.client.get(self.url, parametros).status_code, 200)

    def test_alternar_adicionar_editar_remover(self):
        response = self.client.post(reverse('financeiro:addcalendarioitemview'), {
            'data': '10/11/2026', 'descricao': 'Novo item', 'valor': '1.234,56'})
        item = ItemCalendario.objects.get(descricao='Novo item')
        self.assertEqual(item.valor, Decimal('1234.56'))
        self.assertIn('dia-2026-11-10', response['Location'])

        self.client.post(reverse('financeiro:alternarcalendarioitemview'), {'item': item.pk})
        item.refresh_from_db()
        self.assertTrue(item.concluido)

        self.client.post(reverse('financeiro:editarcalendarioitemview', kwargs={'pk': item.pk}), {
            'data': '11/11/2026', 'descricao': 'Editado'})
        item.refresh_from_db()
        self.assertEqual((item.descricao, item.valor, item.data), ('Editado', None, date(2026, 11, 11)))

        self.client.post(reverse('financeiro:removercalendarioitemview', kwargs={'pk': item.pk}))
        self.assertFalse(ItemCalendario.objects.filter(pk=item.pk).exists())

    def test_programacao(self):
        self.client.post(reverse('financeiro:programacaomesview') + '?ano=2026&mes=11', {'texto': 'Férias'})
        self.assertContains(self.client.get(self.url, {'ano': 2026, 'mes': 11}), 'Férias')

    def test_permissoes(self):
        self.check_user_get_permission(self.url, permission_codename='view_itemcalendario')
        self.check_user_get_permission(reverse('financeiro:addcalendarioitemview'), permission_codename='add_itemcalendario')
        self.check_user_get_permission(reverse('financeiro:importarcalendarioview'), permission_codename='add_itemcalendario')

    def test_alertas(self):
        hoje = date.today()
        ItemCalendario.objects.create(data=hoje - timedelta(days=2), descricao='Atrasado', valor=Decimal('10.00'))
        ItemCalendario.objects.create(data=hoje, descricao='Hoje', valor=Decimal('20.00'))
        ItemCalendario.objects.create(data=hoje + timedelta(days=3), descricao='Em breve', valor=Decimal('30.00'))
        ItemCalendario.objects.create(data=hoje - timedelta(days=2), descricao='Feito', concluido=True)
        ItemCalendario.objects.create(data=hoje - timedelta(days=400), descricao='Historico antigo')
        titulos = ' | '.join(a.titulo for a in agente.regras_calendario(hoje))
        self.assertIn('1 item atrasado', titulos)
        self.assertIn('1 item para hoje', titulos)
        self.assertIn('1 item nos próximos 7 dias', titulos)
