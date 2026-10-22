# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'gerencial'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pagamento/add/', views.pagamento_add, name='pagamento_add'),
    path('pagamento/<int:pk>/edit/', views.pagamento_edit, name='pagamento_edit'),
    path('pagamento/<int:pk>/delete/', views.pagamento_delete, name='pagamento_delete'),
    path('pagamento/<int:pk>/pagar/', views.pagamento_pagar, name='pagamento_pagar'),
    path('importar/', views.importar_planilha, name='importar_planilha'),
]
