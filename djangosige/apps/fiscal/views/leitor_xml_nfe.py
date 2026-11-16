"""Leitor mínimo e seguro de NF-e para importação.

Mantém a importação de XML independente da biblioteca legada usada para
assinar, transmitir e consultar notas na SEFAZ.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

from defusedxml import ElementTree as DefusedElementTree
from defusedxml.common import DefusedXmlException


def _nome_local(tag):
    return tag.rsplit('}', 1)[-1]


def _converter_valor(nome, texto):
    if not texto:
        return None

    if nome in ('dhEmi', 'dhSaiEnt'):
        try:
            return datetime.fromisoformat(texto.replace('Z', '+00:00'))
        except ValueError:
            return texto

    if nome == 'dVenc':
        try:
            return date.fromisoformat(texto)
        except ValueError:
            return texto

    if len(nome) > 1 and nome[0] in ('p', 'q', 'v') and nome[1].isupper():
        try:
            return Decimal(texto)
        except InvalidOperation:
            return texto

    return texto


class SelecaoXML(object):

    def __init__(self, elementos=None, valores=None):
        self._elementos = list(elementos or [])
        self._valores = list(valores or [])

    @property
    def valor(self):
        if self._valores:
            return self._valores[0]
        if not self._elementos:
            return None
        texto = self._elementos[0].text
        texto = texto.strip() if texto and texto.strip() else None
        return _converter_valor(_nome_local(self._elementos[0].tag), texto)

    @property
    def xml(self):
        if not self._elementos:
            return None
        return ElementTree.tostring(
            self._elementos[0],
            encoding='unicode',
        )

    @property
    def regime_tributario(self):
        for elemento in self._elementos:
            for descendente in elemento.iter():
                if _nome_local(descendente.tag).startswith('ICMSSN'):
                    return 1
        return 3

    def __getattr__(self, nome):
        filhos = []
        for elemento in self._elementos:
            filhos.extend(
                filho for filho in list(elemento)
                if _nome_local(filho.tag) == nome
            )

        if not filhos:
            for elemento in self._elementos:
                filhos.extend(
                    descendente for descendente in elemento.iter()
                    if (descendente is not elemento
                        and _nome_local(descendente.tag) == nome)
                )

        if filhos:
            return SelecaoXML(elementos=filhos)

        valores = []
        for elemento in self._elementos:
            for atributo, valor in elemento.attrib.items():
                if _nome_local(atributo) == nome:
                    valores.append(valor)

        return SelecaoXML(valores=valores)

    def __iter__(self):
        for elemento in self._elementos:
            yield SelecaoXML(elementos=[elemento])

    def __len__(self):
        return len(self._elementos) or len(self._valores)


class LeitorXMLNFe(object):

    def __init__(self):
        self._raiz = SelecaoXML()
        self._xml = None

    @property
    def xml(self):
        return self._xml

    @xml.setter
    def xml(self, conteudo):
        if isinstance(conteudo, str):
            conteudo = conteudo.encode('utf-8')
        try:
            raiz = DefusedElementTree.fromstring(conteudo)
        except (DefusedXmlException, ParseError, TypeError, ValueError) as exc:
            raise ValueError(
                'O conteúdo não é um XML válido ou seguro.') from exc
        self._xml = conteudo
        self._raiz = SelecaoXML(elementos=[raiz])

    def __getattr__(self, nome):
        return getattr(self._raiz, nome)
