# -*- coding: utf-8 -*-

from django.urls import re_path as url
from . import views

app_name = 'importacao'
urlpatterns = [
    url(r'^$', views.ProcessoListView.as_view(), name='listaprocessosview'),
    url(r'^adicionar/$', views.AdicionarProcessoView.as_view(), name='addprocessoview'),
    url(r'^processo/(?P<pk>[0-9]+)/$', views.ProcessoView.as_view(), name='processoview'),
    url(r'^processo/(?P<pk>[0-9]+)/editar/$', views.EditarProcessoView.as_view(), name='editarprocessoview'),
    url(r'^documento/(?P<pk>[0-9]+)/$', views.DocumentoView.as_view(), name='documentoview'),
]
