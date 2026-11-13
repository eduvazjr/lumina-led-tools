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
    path('pagamentos/novo/', views.pagamento_negociacao_add, name='pagamento_negociacao_add'),
    path('pagamentos/<int:pk>/', views.pagamento_negociacao_edit, name='pagamento_negociacao_edit'),
    path('pagamentos/<int:pk>/comprovante/', views.pagamento_negociacao_comprovante, name='pagamento_negociacao_comprovante'),
    path('pagamentos/<int:pk>/remover/', views.pagamento_negociacao_remover, name='pagamento_negociacao_remover'),
]
