import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

DADOS = {
    'titulo': 'Contas a pagar', 'subtitulo': 'Finanças · Situação: Aberta',
    'colunas': ['Descrição', 'Vencimento', 'Valor'], 'alinhamentos': ['esquerda', 'esquerda', 'direita'],
    'linhas': [['Frete marítimo; Santos', '06/11/2026', 'R$ 18.430,00'], ['Ajuste', '07/11/2026', '-R$ 1.234,56']],
    'rodape': ['Total', '', 'R$ 17.195,44'],
}


class ExportarTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('exporta', password='senha-teste')
        self.client.force_login(self.user)

    def _post(self, formato, dados=DADOS):
        arquivo = SimpleUploadedFile('dados.json', json.dumps(dados).encode('utf-8'), content_type='application/json')
        return self.client.post(reverse('base:exportar', args=[formato]), {'dados': arquivo})

    def test_csv_abre_no_excel_em_portugues(self):
        r = self._post('csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('attachment; filename="contas-a-pagar-', r['Content-Disposition'])
        conteudo = r.content.decode('utf-8')
        self.assertTrue(conteudo.startswith('﻿'))
        linhas = conteudo.lstrip('﻿').splitlines()
        self.assertEqual(linhas[0], 'Descrição;Vencimento;Valor')
        self.assertEqual(linhas[1], '"Frete marítimo; Santos";06/11/2026;18430,00')
        self.assertEqual(linhas[2], 'Ajuste;07/11/2026;-1234,56')
        self.assertEqual(linhas[3], 'Total;;17195,44')

    def test_pdf_e_gerado(self):
        r = self._post('pdf')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_pdf_nao_busca_recurso_externo(self):
        dados = dict(DADOS, titulo='<img src="http://169.254.169.254/x"> Título')
        r = self._post('pdf', dados)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_exige_login_e_dados_validos(self):
        self.assertEqual(self._post('csv', {'colunas': []}).status_code, 400)
        self.client.logout()
        self.assertEqual(self._post('csv').status_code, 302)
