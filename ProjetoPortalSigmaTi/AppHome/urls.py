from django.urls import path
from . import views

app_name = "AppHome"

urlpatterns = [
    # Página inicial opcional (pode redirecionar para listar_demandas)
    path('', views.home, name='home'),  # agora /AppHome/ funciona
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),
    
    # CRUD de demandas
    path('nova_demanda/', views.nova_demanda, name='nova_demanda'),
    path('listar_demandas/', views.listar_demandas, name='listar_demandas'),
    path('detalhar_demanda/<int:id>/', views.detalhar_demanda, name='detalhar_demanda'),
    path('editar_demanda/<int:id>/', views.editar_demanda, name='editar_demanda'),
    path('excluir_demanda/<int:id>/', views.excluir_demanda, name='excluir_demanda'),

    # Listagem de serviços
    path('listar_servicos/', views.listar_servicos, name='listar_servicos'),

    path('accounts/logout/', views.logout_get, name='logout_get'),
]
