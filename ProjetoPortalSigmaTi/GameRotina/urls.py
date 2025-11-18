from django.urls import path
from . import views

app_name = 'GameRotina'

urlpatterns = [
    path('dashboard_jogo/', views.dashboard_jogo, name='dashboard_jogo'), 
    path('jogo',views.jogo,name='jogo'),
    path("salvar_referencia/", views.salvar_referencia, name="salvar_referencia"),
    path("verificar_item/", views.verificar_item, name="verificar_item"),  # 👈 novo nome aqui
]