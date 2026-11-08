import io
import zipfile
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .drive_negotiations import build_dashboard_data, load_negotiations, parse_xlsx
from .templatetags.gerencial_format import ptbr_currency, ptbr_number


HEADERS = (
    'Nº PEDIDO', 'PRODUTO', 'QUANTIDADE', 'VALOR UNITÁRIO', 'VALOR TOTAL',
    'VALOR PARCELA', 'QTD. PARCELAS', 'PARCELAS PAGAS', 'VENCIMENTO',
)


class BrazilianNumberFormatTests(SimpleTestCase):
    def test_formats_currency_with_thousands_points_and_decimal_comma(self):
        self.assertEqual(ptbr_currency('377407994.15'), 'R$ 377.407.994,15')

    def test_formats_numbers_with_requested_decimal_places(self):
        self.assertEqual(ptbr_number('1527.5', 2), '1.527,50')
        self.assertEqual(ptbr_number('1527.5', 0), '1.528')


def make_xlsx(rows, extra_sheets=None):
    strings = []
    indexes = {}

    def shared(value):
        value = str(value)
        if value not in indexes:
            indexes[value] = len(strings)
            strings.append(value)
        return indexes[value]

    sheets = [('Negociacoes knakasaki', rows)] + list((extra_sheets or {}).items())

    def sheet_xml(sheet_rows):
        xml_rows = []
        for row_number, row in enumerate(sheet_rows, 1):
            cells = []
            for column, value in row.items():
                if isinstance(value, str):
                    cells.append('<c r="%s%d" t="s"><v>%d</v></c>' % (
                        column, row_number, shared(value)))
                else:
                    cells.append('<c r="%s%d"><v>%s</v></c>' % (
                        column, row_number, value))
            xml_rows.append('<row r="%d">%s</row>' % (row_number, ''.join(cells)))
        return '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % ''.join(xml_rows)

    rendered_sheets = [sheet_xml(sheet_rows) for _, sheet_rows in sheets]
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        sheet_entries = ''.join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (name, number, number) for number, (name, _) in enumerate(sheets, 1))
        relationships = ''.join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (number, number) for number in range(1, len(sheets) + 1))
        archive.writestr('xl/workbook.xml', '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>%s</sheets></workbook>' % sheet_entries)
        archive.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s</Relationships>' % relationships)
        archive.writestr('xl/sharedStrings.xml', '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">%s</sst>' % ''.join('<si><t>%s</t></si>' % value for value in strings))
        for number, rendered_sheet in enumerate(rendered_sheets, 1):
            archive.writestr('xl/worksheets/sheet%d.xml' % number, rendered_sheet)
    return output.getvalue()


class NegotiationsParserTests(SimpleTestCase):
    def test_parses_all_supplier_sheets_regions_and_excel_dates(self):
        header_row = {}
        for offset, header in enumerate(HEADERS):
            header_row[chr(ord('A') + offset)] = header
            header_row[chr(ord('L') + offset)] = header
        workbook = make_xlsx([
            header_row,
            {'A': 'PED-1', 'B': 'Produto A', 'C': 2, 'D': 50, 'E': 100, 'F': 25, 'G': 4, 'H': 1, 'I': 46000},
            {'L': 'PED-2', 'M': 'Produto B', 'N': 1, 'O': 200, 'P': 200, 'Q': 100, 'R': 2, 'S': 2, 'T': 46001},
        ], {'Amarante': [header_row, {'A': 'PED-3', 'B': 'Produto C', 'E': 50, 'F': 50, 'G': 1, 'H': 0, 'I': 46002}]})

        records = parse_xlsx(workbook)

        self.assertEqual([record['order_number'] for record in records], ['PED-1', 'PED-2', 'PED-3'])
        self.assertEqual([record['supplier'] for record in records], ['Negociacoes knakasaki', 'Negociacoes knakasaki', 'Amarante'])
        self.assertEqual(records[0]['due_date'], date(2025, 12, 9))
        self.assertEqual(records[1]['paid_installments'], 2)

    def test_normalises_purchase_and_payment_supplier_layout(self):
        workbook = make_xlsx([], {
            'Amarante': [
                {'B': 'Compras', 'F': 'Pagamentos'},
                {'B': 'Data', 'C': 'Descrição ', 'D': 'Valor', 'F': 'Data', 'G': 'Descrição ', 'H': 'Valor'},
                {'B': 46000, 'C': 'Lote A', 'D': 1000, 'F': 46010, 'G': 'Pix', 'H': 250},
            ],
        })

        records = parse_xlsx(workbook)
        data = build_dashboard_data(records, today=date(2025, 12, 1))

        self.assertEqual(records[0]['supplier'], 'Amarante')
        self.assertEqual(records[0]['product'], 'Lote A')
        self.assertEqual(data['supplier_kpis']['Amarante']['total_negotiated'], 1000)
        self.assertEqual(data['supplier_kpis']['Amarante']['received_estimate'], 250)

    def test_builds_financial_and_installment_kpis(self):
        records = [
            {'supplier': 'Amarante', 'order_number': '1', 'product': 'A', 'total_value': 100, 'installment_value': 25, 'installment_count': 4, 'paid_installments': 1, 'due_date': date(2025, 1, 1)},
            {'supplier': 'Nakasaki', 'order_number': '2', 'product': 'B', 'total_value': 200, 'installment_value': 100, 'installment_count': 2, 'paid_installments': 2, 'due_date': date(2025, 2, 1)},
        ]

        data = build_dashboard_data(records, today=date(2025, 1, 15))

        self.assertEqual(data['kpis']['total_negotiated'], 300)
        self.assertEqual(data['kpis']['received_estimate'], 225)
        self.assertEqual(data['kpis']['outstanding_balance'], 75)
        self.assertEqual(data['kpis']['order_count'], 2)
        self.assertEqual(data['kpis']['overdue_installments'], 3)
        self.assertEqual(data['supplier_kpis']['Amarante']['total_negotiated'], 100)


@override_settings(GOOGLE_DRIVE_FILE_ID='file-id', GOOGLE_DRIVE_CREDENTIALS_FILE='credential.json')
class NegotiationsCacheTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @patch('djangosige.apps.gerencial.drive_negotiations.download_drive_file')
    def test_caches_successful_result_for_300_seconds(self, download):
        download.return_value = make_xlsx([])
        first = load_negotiations()
        second = load_negotiations()
        self.assertEqual(first, second)
        self.assertEqual(download.call_count, 1)

    @patch('djangosige.apps.gerencial.drive_negotiations.download_drive_file')
    def test_returns_stale_cache_when_refresh_fails(self, download):
        cache.set('gerencial:negotiations:last-good', {'records': [], 'synced_at': 'previous'}, None)
        download.side_effect = RuntimeError('Drive indisponível')
        result = load_negotiations()
        self.assertTrue(result['is_stale'])
        self.assertIn('Drive indisponível', result['sync_error'])


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='gerencial_tester', password='test-password-only')
        self.url = reverse('gerencial:dashboard')

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    @patch('djangosige.apps.gerencial.views.load_negotiations')
    def test_dashboard_renders_drive_negotiations_sections(self, load):
        load.return_value = {'records': [], 'synced_at': '2026-11-07T12:00:00-03:00', 'is_stale': False, 'sync_error': ''}
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gerencial/dashboard.html')
        self.assertContains(response, 'Negociações com fornecedores')
        self.assertContains(response, 'class="kpi-grid"')
        self.assertContains(response, 'grid-template-columns:repeat(3,minmax(0,1fr))')
        self.assertContains(response, 'id="chartDist"')
        self.assertContains(response, 'id="chartVenc"')
        self.assertContains(response, 'vendor/chartjs/chart.umd.min.js')
        self.assertNotContains(response, 'cdn.jsdelivr.net')

    @patch('djangosige.apps.gerencial.views.load_negotiations')
    def test_dashboard_shows_graceful_sync_error(self, load):
        load.return_value = {'records': [], 'synced_at': None, 'is_stale': False, 'sync_error': 'Credenciais do Google Drive não configuradas.'}
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciais do Google Drive não configuradas.')
