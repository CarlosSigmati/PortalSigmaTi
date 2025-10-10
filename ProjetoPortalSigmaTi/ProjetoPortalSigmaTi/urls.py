from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from AppHome import views as home_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('AppHome.urls')),  # inclui as URLs do AppHome
    path('AppHome/', RedirectView.as_view(pattern_name='AppHome:dashboard', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),
 
]
