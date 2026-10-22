# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'financeiro_grupo'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transferencia/add/', views.transferencia_add, name='transferencia_add'),
    path('transferencia/<int:pk>/edit/', views.transferencia_edit, name='transferencia_edit'),
    path('transferencia/<int:pk>/', views.transferencia_detail, name='transferencia_detail'),
    path('transferencia/<int:pk>/confirmar/', views.transferencia_confirmar, name='transferencia_confirmar'),
    path('relatorio/', views.relatorio, name='relatorio'),
]
