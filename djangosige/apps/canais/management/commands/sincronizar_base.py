# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from djangosige.apps.canais.baselinker import sincronizar


class Command(BaseCommand):
    help = 'Busca pedidos e devoluções no Base.com (BaseLinker) e atualiza as métricas dos canais de venda.'

    def add_arguments(self, parser):
        parser.add_argument('--desde', help='Data inicial (AAAA-MM-DD) para carregar ou refazer um período.')

    def handle(self, *args, **opcoes):
        desde = None
        if opcoes.get('desde'):
            try:
                desde = datetime.strptime(opcoes['desde'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Use a data no formato AAAA-MM-DD, por exemplo 2026-10-01.')
        self.stdout.write('Sincronizando com o Base.com... (pode levar alguns minutos)')
        registro = sincronizar(desde=desde)
        self.stdout.write('%d pedidos e %d devoluções lidos em %d chamadas.' % (
            registro.pedidos, registro.devolucoes, registro.chamadas))
        if registro.erro:
            raise CommandError(registro.erro)
        self.stdout.write(self.style.SUCCESS('Pronto.'))
