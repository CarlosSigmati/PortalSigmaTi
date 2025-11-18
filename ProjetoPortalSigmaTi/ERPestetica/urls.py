from django.urls import path
from . import views
from .views import servicos_por_profissional

app_name = 'ERPestetica'  

urlpatterns = [
    path("", views.lista_agendamentos, name="lista_agendamentos"),
    path("novo/", views.criar_agendamento, name="criar_agendamento"),
    path("agendamento/<int:pk>/", views.detalhe_agendamento, name="detalhe_agendamento"),
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("clientes/criar/", views.criar_cliente, name="criar_cliente"),
    path("clientes/<int:pk>/editar/", views.editar_cliente, name="editar_cliente"),
    path("clientes/<int:pk>/excluir/", views.excluir_cliente, name="excluir_cliente"),
    path('agendamento/<int:pk>/alterar-status/', views.alterar_status, name='alterar_status'),

    path("horarios_disponiveis/", views.horarios_disponiveis, name="horarios_disponiveis"),

    path("servicos_por_profissional/", servicos_por_profissional, name="servicos_por_profissional"),

    
]
