# -*- coding: utf-8 -*-

from django.urls import re_path as url
from . import views
from .exportar import exportar

from djangosige.configs import DEBUG

app_name = 'base'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^alertas/$', views.AlertasView.as_view(), name='alertasview'),
    url(r'^importacao/(?P<tipo>[\w-]+)/$', views.ImportacaoView.as_view(), name='importacaoview'),
    url(r'^exportar/(?P<formato>csv|pdf)/$', exportar, name='exportar'),
]

if DEBUG:
    urlpatterns += [
        url(r'^404/$', views.handler404),
        url(r'^500/$', views.handler500),
    ]
