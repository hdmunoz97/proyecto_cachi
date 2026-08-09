from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esto conecta el proyecto principal con tu aplicación
    path('', include('control_jornada.urls')),
]