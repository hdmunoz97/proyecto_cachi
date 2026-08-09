from django.urls import path
from . import views

urlpatterns = [
    # Vista A: Dashboard
    path('', views.dashboard_jefatura, name='dashboard_jefatura'),
    
    # Vista B: Registro
    path('registro/', views.registro_turno, name='registro_turno'),
    
    # Vista C: RRHH
    path('rrhh/', views.panel_rrhh, name='panel_rrhh'),

    # Vista D: Bloquear/Desbloquear asignación del empleado
    path('bloquear/<int:id_empleado>/', views.alternar_bloqueo, name='alternar_bloqueo'),

    # Vista E: Eliminar alerta del panel interactivo (Nueva implementación)
    path('alerta/eliminar/<int:id_alerta>/', views.eliminar_alerta, name='eliminar_alerta'),

    #alerta popup
    path('verificar_empleado/<str:documento>/', views.verificar_empleado, name='verificar_empleado'),
]
