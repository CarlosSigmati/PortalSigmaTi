from django.urls import path
from . import views

app_name = 'GameRotina'

urlpatterns = [
    path('dashboard_jogo/', views.dashboard_jogo, name='dashboard_jogo'), 
    path('jogo',views.jogo,name='jogo'),
]