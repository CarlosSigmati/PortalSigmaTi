from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from AppHome import views as home_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('AppHome.urls')),  # inclui as URLs do AppHome
    path('AppHome/', RedirectView.as_view(pattern_name='AppHome:dashboard', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),

    path('GameRotina/', include('GameRotina.urls')),  # inclui as URLs do GameRotina
    
    path('ERPestetica/', include('ERPestetica.urls', namespace='agendamentos')), 

   path('anamnese/', include('Exames.urls', namespace='Exames')),  # inclui o app Exames

]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)