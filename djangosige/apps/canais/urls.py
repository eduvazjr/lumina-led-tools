# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'canais'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('sincronizar/', views.sincronizar_agora, name='sincronizar'),
    path('contas/', views.contas, name='contas'),
]
