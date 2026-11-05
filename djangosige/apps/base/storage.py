# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class DocumentosPrivadosStorage(FileSystemStorage):
    """Guarda arquivos fora de MEDIA_ROOT, que o servidor publica sem exigir login."""

    @property
    def base_location(self):
        return settings.DOCUMENTOS_PRIVADOS_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)
