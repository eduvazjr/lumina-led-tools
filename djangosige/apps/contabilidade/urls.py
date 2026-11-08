# -*- coding: utf-8 -*-

from django.urls import re_path as url
from . import views, empresas

app_name = 'contabilidade'

urlpatterns = [
    # Dashboard principal
    # Contabilidade interna por empresa do grupo
    url(r'^$', empresas.painel, name='dashboard'),
    url(r'^empresa/(?P<empresa_id>[0-9]+)/$', empresas.empresa, name='empresa'),
    url(r'^empresa/(?P<empresa_id>[0-9]+)/dados/(?P<area>fiscal|contabil|dp)/$', empresas.dados, name='dados_empresa'),
    url(r'^empresa/(?P<empresa_id>[0-9]+)/(?P<tipo>[a-z]+)/novo/$', empresas.registro, name='novo_registro'),
    url(r'^empresa/(?P<empresa_id>[0-9]+)/(?P<tipo>[a-z]+)/(?P<pk>[0-9]+)/$', empresas.registro, name='editar_registro'),
    url(r'^empresa/(?P<empresa_id>[0-9]+)/(?P<tipo>[a-z]+)/(?P<pk>[0-9]+)/remover/$', empresas.remover_registro, name='remover_registro'),
    
    # Processos
    url(r'^processos/$', views.lista_processos, name='lista_processos'),
    url(r'^processos/novo/$', views.novo_processo, name='novo_processo'),
    url(r'^processos/(?P<pk>[0-9]+)/$', views.detalhe_processo, name='detalhe_processo'),
    url(r'^processos/(?P<pk>[0-9]+)/editar/$', views.editar_processo, name='editar_processo'),
    
    # Módulo 1: Entrada de Cliente
    url(r'^entrada/(?P<processo_id>[0-9]+)/$', views.entrada_cliente, name='entrada_cliente'),
    
    # Módulo 2: Legalização
    url(r'^legalizacao/(?P<processo_id>[0-9]+)/$', views.legalizacao, name='legalizacao'),
    
    # Módulo 3: Departamento Pessoal
    url(r'^dp/(?P<processo_id>[0-9]+)/$', views.departamento_pessoal, name='departamento_pessoal'),
    url(r'^dp/(?P<dp_id>[0-9]+)/funcionarios/$', views.funcionarios, name='rh_dp_funcionarios'),
    url(r'^dp/(?P<dp_id>[0-9]+)/folha/$', views.folha_pagamento, name='rh_dp_folhas'),
    
    # Módulo 4: Fiscal
    url(r'^fiscal/(?P<processo_id>[0-9]+)/$', views.fiscal, name='fiscal'),
    url(r'^fiscal/(?P<fiscal_id>[0-9]+)/apuracao/$', views.apuracao_tributos, name='apuracao_tributos'),
    url(r'^fiscal/(?P<fiscal_id>[0-9]+)/obrigacoes/$', views.obrigacoes_acessorias, name='obrigacoes_acessorias'),
    
    # Módulo 5: Contábil
    url(r'^contabil/(?P<processo_id>[0-9]+)/$', views.contabil, name='contabil'),
    url(r'^contabil/(?P<contabil_id>[0-9]+)/lancamentos/$', views.lancamentos_contabeis, name='lancamentos_contabeis'),
    url(r'^contabil/(?P<contabil_id>[0-9]+)/conciliacao/$', views.conciliacao_bancaria, name='conciliacao_bancaria'),
    url(r'^contabil/(?P<contabil_id>[0-9]+)/dre/$', views.demonstracao_resultado, name='demonstracao_resultado'),
    
    # RH: visão geral de todos os clientes
    url(r'^rh/funcionarios/$', views.rh_funcionarios, name='rh_funcionarios'),
    url(r'^rh/folhas/$', views.rh_folhas, name='rh_folhas'),
    url(r'^rh/departamentos/$', views.rh_departamentos, name='rh_departamentos'),

    # Relatórios
    url(r'^relatorios/$', views.relatorios, name='relatorios'),
    url(r'^relatorios/processos/$', views.relatorio_processos, name='relatorio_processos'),
    url(r'^relatorios/fiscal/$', views.relatorio_fiscal, name='relatorio_fiscal'),
]
