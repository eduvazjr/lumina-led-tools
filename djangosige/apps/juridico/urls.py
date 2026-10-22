# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'juridico'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('processo/add/', views.processo_add, name='processo_add'),
    path('processo/<int:pk>/edit/', views.processo_edit, name='processo_edit'),
    path('processo/<int:pk>/', views.processo_detail, name='processo_detail'),
    path('processo/<int:pk>/alertar/', views.alertar_diretoria, name='alertar_diretoria'),
    path('pesquisar/', views.pesquisar_processos, name='pesquisar_processos'),
    path('relatorio-risco/', views.relatorio_risco, name='relatorio_risco'),
]
