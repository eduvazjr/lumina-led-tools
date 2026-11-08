from django.urls import path

from . import views

app_name = 'anexos'
urlpatterns = [
    path('enviar/<int:content_type_id>/<int:object_id>/', views.enviar, name='enviar'),
    path('<int:pk>/', views.baixar, name='baixar'),
    path('<int:pk>/remover/', views.remover, name='remover'),
]
