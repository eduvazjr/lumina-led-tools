from datetime import datetime
from decimal import Decimal

from django.test import SimpleTestCase

from djangosige.apps.fiscal.views.leitor_xml_nfe import LeitorXMLNFe


XML_NFE = b'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe Id="NFe35261111111111111111550010000001231000001234">
      <ide>
        <nNF>123</nNF>
        <serie>1</serie>
        <dhEmi>2026-11-16T10:30:00-03:00</dhEmi>
      </ide>
      <emit><CNPJ>11111111111111</CNPJ></emit>
      <dest><CNPJ>22222222222222</CNPJ></dest>
      <det nItem="1">
        <prod><cProd>A1</cProd><xProd>Produto A</xProd><vProd>10.50</vProd></prod>
        <imposto><ICMS><ICMS00><orig>0</orig><CST>00</CST><pICMS>18.00</pICMS></ICMS00></ICMS></imposto>
      </det>
      <det nItem="2">
        <prod><cProd>B2</cProd><xProd>Produto B</xProd></prod>
        <imposto><ICMS><ICMSSN102><orig>0</orig><CSOSN>102</CSOSN></ICMSSN102></ICMS></imposto>
      </det>
    </infNFe>
  </NFe>
</nfeProc>'''


class LeitorXMLNFeTestCase(SimpleTestCase):

    def test_le_campos_com_namespace_e_atributos(self):
        nfe = LeitorXMLNFe()
        nfe.xml = XML_NFE

        self.assertEqual(nfe.infNFe.ide.nNF.valor, '123')
        self.assertEqual(nfe.infNFe.emit.CNPJ.valor, '11111111111111')
        self.assertEqual(
            nfe.infNFe.Id.valor,
            'NFe35261111111111111111550010000001231000001234',
        )

    def test_permite_iterar_itens_e_ler_grupo_icms(self):
        nfe = LeitorXMLNFe()
        nfe.xml = XML_NFE
        itens = list(nfe.infNFe.det)

        self.assertEqual(len(itens), 2)
        self.assertEqual(itens[0].prod.xProd.valor, 'Produto A')
        self.assertEqual(itens[0].imposto.ICMS.CST.valor, '00')
        self.assertEqual(itens[0].imposto.ICMS.regime_tributario, 3)
        self.assertEqual(itens[1].imposto.ICMS.CSOSN.valor, '102')
        self.assertEqual(itens[1].imposto.ICMS.regime_tributario, 1)

    def test_converte_datas_e_valores_numericos(self):
        nfe = LeitorXMLNFe()
        nfe.xml = XML_NFE
        item = list(nfe.infNFe.det)[0]

        self.assertEqual(
            nfe.infNFe.ide.dhEmi.valor,
            datetime.fromisoformat('2026-11-16T10:30:00-03:00'),
        )
        self.assertEqual(item.prod.vProd.valor, Decimal('10.50'))
        self.assertEqual(item.imposto.ICMS.pICMS.valor, Decimal('18.00'))

    def test_campo_ausente_retorna_none(self):
        nfe = LeitorXMLNFe()
        nfe.xml = XML_NFE

        self.assertIsNone(nfe.infNFe.cobr.fat.nFat.valor)
        self.assertIsNone(nfe.infNFe.cobr.xml)

    def test_rejeita_entidade_externa(self):
        xml_inseguro = b'''<?xml version="1.0"?>
        <!DOCTYPE NFe [<!ENTITY arquivo SYSTEM "file:///etc/passwd">]>
        <NFe><infNFe><ide><nNF>&arquivo;</nNF></ide></infNFe></NFe>'''

        nfe = LeitorXMLNFe()
        with self.assertRaisesRegex(ValueError, 'XML válido ou seguro'):
            nfe.xml = xml_inseguro
