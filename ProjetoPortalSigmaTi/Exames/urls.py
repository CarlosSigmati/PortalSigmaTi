from django.urls import path
from . import views

app_name = 'Exames'

urlpatterns = [
    path('anamnese/', views.anamnese_view, name='anamnese'),
    path('crud/', views.exames_crud, name='exames_crud'),
    path('excluir/<int:exame_id>/', views.excluir_exame, name='excluir_exame'),
    path('imprimir/<int:exame_id>/', views.imprimir_exame, name='imprimir_exame'),
]
