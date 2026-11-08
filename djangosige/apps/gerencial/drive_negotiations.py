import base64
import json
import os
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from xml.etree import ElementTree

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

CACHE_KEY = 'gerencial:negotiations:v2'
LAST_GOOD_KEY = 'gerencial:negotiations:last-good'
CACHE_SECONDS = 300
EXPECTED_SUPPLIERS = (
    'Negociacoes knakasaki', 'Amarante', 'Nakasaki', 'Lucas',
    'Terra 2025', 'Terra 2026', 'Max', 'Yé',
)
XML_NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
OFFICE_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
FIELDS = (
    'order_number', 'product', 'quantity', 'unit_value', 'total_value',
    'installment_value', 'installment_count', 'paid_installments', 'due_date',
)
HEADER_ALIASES = {
    'N PEDIDO': 'order_number', 'NO PEDIDO': 'order_number', 'PEDIDO': 'order_number',
    'PRODUTO': 'product', 'QUANTIDADE': 'quantity', 'QTD': 'quantity',
    'VALOR UNITARIO': 'unit_value', 'VL UNITARIO': 'unit_value',
    'VALOR TOTAL': 'total_value', 'TOTAL': 'total_value',
    'VALOR PARCELA': 'installment_value', 'VL PARCELA': 'installment_value',
    'QTD PARCELAS': 'installment_count', 'PARCELAS': 'installment_count',
    'PARCELAS PAGAS': 'paid_installments', 'QTD PAGAS': 'paid_installments',
    'VENCIMENTO': 'due_date', 'DATA VENCIMENTO': 'due_date',
}


def _b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=')


def _service_account_token(credentials_path):
    try:
        with open(credentials_path, encoding='utf-8') as credential_file:
            credentials = json.load(credential_file)
    except (OSError, ValueError) as exc:
        raise RuntimeError('Não foi possível ler as credenciais do Google Drive: %s' % exc)

    now = int(time.time())
    header = _b64url(json.dumps({'alg': 'RS256', 'typ': 'JWT'}, separators=(',', ':')).encode())
    claims = _b64url(json.dumps({
        'iss': credentials['client_email'],
        'scope': 'https://www.googleapis.com/auth/drive.readonly',
        'aud': credentials.get('token_uri', 'https://oauth2.googleapis.com/token'),
        'iat': now,
        'exp': now + 3600,
    }, separators=(',', ':')).encode())
    signing_input = header + b'.' + claims

    key_path = None
    try:
        credential_directory = os.path.dirname(os.path.abspath(credentials_path))
        with tempfile.NamedTemporaryFile(
            'w', suffix='.pem', delete=False, encoding='utf-8', dir=credential_directory
        ) as key_file:
            key_file.write(credentials['private_key'])
            key_path = key_file.name
        process = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-sign', key_path], input=signing_input,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if process.returncode:
            raise RuntimeError('Falha ao assinar autenticação do Google Drive.')
        assertion = signing_input + b'.' + _b64url(process.stdout)
    except OSError as exc:
        raise RuntimeError('OpenSSL não está disponível para autenticação: %s' % exc)
    finally:
        if key_path:
            try:
                os.unlink(key_path)
            except OSError:
                pass

    body = urllib.parse.urlencode({
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': assertion.decode(),
    }).encode()
    request = urllib.request.Request(credentials.get('token_uri', 'https://oauth2.googleapis.com/token'), data=body)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())['access_token']
    except Exception as exc:
        raise RuntimeError('Falha ao autenticar no Google Drive: %s' % exc)


def download_drive_file(file_id, credentials_path):
    token = _service_account_token(credentials_path)
    url = 'https://www.googleapis.com/drive/v3/files/%s?alt=media' % urllib.parse.quote(file_id, safe='')
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer %s' % token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except Exception as exc:
        raise RuntimeError('Falha ao baixar a planilha do Google Drive: %s' % exc)


def _column_number(reference):
    letters = ''.join(character for character in reference if character.isalpha())
    number = 0
    for character in letters:
        number = number * 26 + ord(character.upper()) - 64
    return number


def _normalise_header(value):
    import unicodedata
    text = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().upper()
    return ' '.join(text.replace('.', ' ').replace('º', ' ').replace('°', ' ').split())


def _decimal(value):
    if value in (None, ''):
        return Decimal('0')
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    text = str(value).strip().replace('R$', '').replace(' ', '')
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal('0')


def _excel_date(value):
    if not value:
        return None
    if isinstance(value, (int, float, Decimal)) or str(value).replace('.', '', 1).isdigit():
        return date(1899, 12, 30) + timedelta(days=int(float(value)))
    for pattern in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y'):
        try:
            return datetime.strptime(str(value).strip(), pattern).date()
        except ValueError:
            pass
    return None


def _read_sheet(archive, target, shared_strings):
    root = ElementTree.fromstring(archive.read(target))
    rows = []
    for row in root.findall('.//x:row', XML_NS):
        values = {}
        for cell in row.findall('x:c', XML_NS):
            value_node = cell.find('x:v', XML_NS)
            if value_node is None:
                continue
            value = value_node.text or ''
            if cell.get('t') == 's':
                value = shared_strings[int(value)]
            values[_column_number(cell.get('r', ''))] = value
        rows.append(values)
    return rows


def _records_from_rows(rows, supplier):
    records = []
    for row_index, row in enumerate(rows):
        mapped_headers = {column: HEADER_ALIASES.get(_normalise_header(value)) for column, value in row.items()}
        starts = [column for column, field in mapped_headers.items() if field == 'order_number']
        for start in starts:
            header_columns = {
                column: mapped_headers[column]
                for column in range(start, start + 9)
                if mapped_headers.get(column)
            }
            if 'product' not in header_columns.values():
                continue
            for data_row in rows[row_index + 1:]:
                if HEADER_ALIASES.get(_normalise_header(data_row.get(start))) == 'order_number':
                    break
                raw = {field: data_row.get(column) for column, field in header_columns.items()}
                if not raw.get('order_number') and not raw.get('product'):
                    continue
                record = {'supplier': supplier}
                record.update(raw)
                for field in ('quantity', 'unit_value', 'total_value', 'installment_value', 'installment_count', 'paid_installments'):
                    record[field] = _decimal(record.get(field))
                record['due_date'] = _excel_date(record.get('due_date'))
                record['order_number'] = str(record.get('order_number') or '').strip()
                record['product'] = str(record.get('product') or '').strip()
                records.append(record)
    return records


def _fallback_records(rows, supplier):
    for row_index, row in enumerate(rows):
        value_columns = [column for column, value in row.items() if _normalise_header(value) == 'VALOR']
        if not value_columns:
            continue
        purchase_value_column = value_columns[0]
        payment_value_column = value_columns[1] if len(value_columns) > 1 else None
        purchase_date_column = purchase_value_column - 2
        purchase_description_column = purchase_value_column - 1
        payment_date_column = payment_value_column - 2 if payment_value_column else None
        payment_description_column = payment_value_column - 1 if payment_value_column else None
        records = []
        for sequence, data_row in enumerate(rows[row_index + 1:], 1):
            purchase_value = _decimal(data_row.get(purchase_value_column))
            payment_value = _decimal(data_row.get(payment_value_column)) if payment_value_column else Decimal('0')
            if not purchase_value and not payment_value:
                continue
            purchase_date = _excel_date(data_row.get(purchase_date_column))
            raw_description = data_row.get(purchase_description_column) or data_row.get(payment_description_column)
            payment_date_raw = data_row.get(payment_date_column) if payment_date_column is not None else None
            if not purchase_date and not (_excel_date(payment_date_raw) if payment_date_raw not in (None, '') else None) and not str(raw_description or '').strip():
                continue  # linha de TOTAL da planilha (sem data e sem descricao)
            description = raw_description or 'Pagamento'
            status = _normalise_header(data_row.get(purchase_value_column + 1))
            if status == 'PAGO' and not payment_value:
                payment_value = purchase_value
            records.append({
                'supplier': supplier,
                'order_number': purchase_date.isoformat() if purchase_date else '%s-%d' % (supplier, sequence),
                'product': str(description).strip(),
                'quantity': Decimal('0'), 'unit_value': Decimal('0'),
                'total_value': purchase_value,
                'installment_value': Decimal('0'), 'installment_count': Decimal('0'),
                'paid_installments': Decimal('0'), 'payment_value': payment_value,
                'due_date': purchase_date or _excel_date(data_row.get(payment_date_column)),
            })
        return records
    return []


def parse_xlsx(content):
    records = []
    with zipfile.ZipFile(BytesIO(content)) as archive:
        shared_strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ElementTree.fromstring(archive.read('xl/sharedStrings.xml'))
            for item in root.findall('x:si', XML_NS):
                shared_strings.append(''.join(node.text or '' for node in item.findall('.//x:t', XML_NS)))
        workbook = ElementTree.fromstring(archive.read('xl/workbook.xml'))
        relations = ElementTree.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {relation.get('Id'): relation.get('Target') for relation in relations.findall('r:Relationship', REL_NS)}
        for sheet in workbook.findall('.//x:sheet', XML_NS):
            supplier = sheet.get('name')
            target = targets.get(sheet.get(OFFICE_REL), '')
            if not target:
                continue
            target = target.lstrip('/')
            if not target.startswith('xl/'):
                target = 'xl/' + target
            rows = _read_sheet(archive, target, shared_strings)
            sheet_records = _records_from_rows(rows, supplier)
            records.extend(sheet_records or _fallback_records(rows, supplier))
    return records


def _kpis(records, today):
    total = sum((_decimal(record.get('total_value')) for record in records), Decimal('0'))
    received = sum((
        _decimal(record.get('payment_value')) if 'payment_value' in record else
        min(_decimal(record.get('paid_installments')), _decimal(record.get('installment_count'))) * _decimal(record.get('installment_value'))
        for record in records
    ), Decimal('0'))
    # Pagamento acima do negociado fica separado: não conta como recebido nem
    # abate saldo em aberto. Por isso os totais gerais devem ser a soma por
    # fornecedor (_sum_kpis), nunca este cálculo sobre todos os registros juntos.
    paid_above = max(Decimal('0'), received - total)
    received = min(received, total)
    overdue = sum(int(max(Decimal('0'), _decimal(record.get('installment_count')) - _decimal(record.get('paid_installments')))) for record in records if record.get('due_date') and record['due_date'] < today)
    upcoming = sum(int(max(Decimal('0'), _decimal(record.get('installment_count')) - _decimal(record.get('paid_installments')))) for record in records if record.get('due_date') and today <= record['due_date'] <= today + timedelta(days=30))
    return {
        'total_negotiated': total, 'received_estimate': received,
        'outstanding_balance': max(Decimal('0'), total - received),
        'paid_above_negotiated': paid_above,
        'order_count': len({(record.get('supplier'), record.get('order_number')) for record in records if _decimal(record.get('total_value')) > 0}),
        'installment_count': sum(int(_decimal(record.get('installment_count'))) for record in records),
        'overdue_installments': overdue, 'upcoming_installments': upcoming,
    }


def _sum_kpis(supplier_kpis):
    fields = (
        'total_negotiated', 'received_estimate', 'outstanding_balance', 'paid_above_negotiated',
        'order_count', 'installment_count', 'overdue_installments', 'upcoming_installments',
    )
    return {field: sum((kpis[field] for kpis in supplier_kpis), Decimal('0') if field in fields[:4] else 0) for field in fields}


def build_dashboard_data(records, today=None):
    today = today or timezone.localdate()
    by_supplier = defaultdict(list)
    for record in records:
        by_supplier[record.get('supplier', 'Não identificado')].append(record)
    suppliers = sorted(set(EXPECTED_SUPPLIERS) | set(by_supplier))
    supplier_kpis = {supplier: _kpis(by_supplier[supplier], today) for supplier in suppliers}
    return {
        'records': records,
        'suppliers': suppliers,
        'kpis': _sum_kpis(supplier_kpis.values()),
        'supplier_kpis': supplier_kpis,
        'chart_distribution': {
            'labels': suppliers,
            'values': [float(supplier_kpis[supplier]['total_negotiated']) for supplier in suppliers],
        },
        'chart_due': {
            'labels': suppliers,
            'values': [supplier_kpis[supplier]['overdue_installments'] for supplier in suppliers],
        },
    }


def load_negotiations():
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached
    file_id = getattr(settings, 'GOOGLE_DRIVE_FILE_ID', '')
    credentials_path = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS_FILE', '')
    try:
        if not file_id:
            raise RuntimeError('Arquivo do Google Drive não configurado.')
        if not credentials_path:
            raise RuntimeError('Credenciais do Google Drive não configuradas.')
        content = download_drive_file(file_id, credentials_path)
        result = {
            'records': parse_xlsx(content),
            'synced_at': timezone.now().isoformat(),
            'is_stale': False,
            'sync_error': '',
        }
        cache.set(CACHE_KEY, result, CACHE_SECONDS)
        cache.set(LAST_GOOD_KEY, result, None)
        return result
    except Exception as exc:
        stale = cache.get(LAST_GOOD_KEY)
        if stale:
            result = dict(stale)
            result.update({'is_stale': True, 'sync_error': str(exc)})
            return result
        return {'records': [], 'synced_at': None, 'is_stale': False, 'sync_error': str(exc)}
