# -*- coding: utf-8 -*-
"""Documentos anexados a qualquer registro do sistema (cliente, pedido, nota...).

O arquivo fica em DOCUMENTOS_PRIVADOS_ROOT, fora da pasta pública de mídia,
e só é aberto pelas telas do sistema, com login e permissão no registro.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from djangosige.apps.base.storage import DocumentosPrivadosStorage


class Anexo(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    objeto = GenericForeignKey('content_type', 'object_id')
    arquivo = models.FileField(upload_to='anexos/%Y/%m/', storage=DocumentosPrivadosStorage())
    nome = models.CharField(max_length=255)
    tamanho = models.PositiveIntegerField(default=0)
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento anexado'
        verbose_name_plural = 'Documentos anexados'
        ordering = ['-enviado_em', '-id']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return self.nome

    @property
    def extensao(self):
        return self.nome.rsplit('.', 1)[-1].lower() if '.' in self.nome else ''


@receiver(post_delete, sender=Anexo)
def remover_arquivo_anexo(sender, instance, **kwargs):
    instance.arquivo.delete(save=False)
