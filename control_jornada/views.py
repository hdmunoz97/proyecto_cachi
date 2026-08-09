from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from .models import Empleado, RegistroHoras, Alerta, HorasExtra
from datetime import datetime

from django.shortcuts import get_object_or_404, redirect
from .models import Alerta
from django.http import JsonResponse


# VISTA A: Dashboard de Alertas (Jefatura)
def dashboard_jefatura(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                e.id_empleado,
                e.nombre || ' ' || e.apellido AS mecanico,
                e.cargo,
                COALESCE(SUM(r.horas_trabajadas), 0) AS horas_semanales,
                e.max_horas_semanales,
                CASE 
                    WHEN COALESCE(SUM(r.horas_trabajadas), 0) > e.max_horas_semanales THEN 'Alerta Crítica: Exceso de Jornada'
                    WHEN COALESCE(SUM(r.horas_trabajadas), 0) >= (e.max_horas_semanales * 0.8) THEN 'Atención: Cerca del Límite'
                    ELSE 'Jornada Normal'
                END AS estado_salud_laboral,
                e.bloqueado -- <-- AQUÍ TRAEMOS EL ESTADO REAL DE LA BASE DE DATOS
            FROM empleados e
            LEFT JOIN registro_horas r 
                ON e.id_empleado = r.id_empleado 
               AND r.fecha BETWEEN DATE_TRUNC('week', CURRENT_DATE)::DATE 
                               AND (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::DATE
            GROUP BY e.id_empleado, e.nombre, e.apellido, e.cargo, e.max_horas_semanales, e.bloqueado; -- <-- Y LO AGRUPAMOS AQUÍ
        """)
        datos_dashboard = cursor.fetchall()

    context = {
        'datos': datos_dashboard
    }
    return render(request, 'control_jornada/dashboard.html', context)


# VISTA B: Módulo de Registro de Turno (Mecánico)[cite: 1]
def registro_turno(request):
    if request.method == 'POST':
        # Capturamos los datos del formulario. El documento se recibe como entrada de texto.
        documento_texto = request.POST.get('documento_empleado')
        hora_entrada = request.POST.get('hora_entrada')
        hora_salida = request.POST.get('hora_salida')
        horas_trabajadas = request.POST.get('horas_trabajadas')

        try:
            # Buscamos al empleado por el texto de su documento
            empleado = Empleado.objects.get(documento=documento_texto)
            
            # Guardamos el registro. El trigger de la BD actuará automáticamente si hay exceso[cite: 2]
            RegistroHoras.objects.create(
                id_empleado=empleado,
                fecha=datetime.now().date(),
                hora_entrada=hora_entrada,
                hora_salida=hora_salida,
                horas_trabajadas=horas_trabajadas
            )
            return redirect('dashboard_jefatura')
            
        except Empleado.DoesNotExist:
            # Si el documento ingresado no existe, recargamos con error
            context = {'error': 'No se encontró un empleado con ese documento.'}
            return render(request, 'control_jornada/registro_turno.html', context)

    return render(request, 'control_jornada/registro_turno.html')


# VISTA C: Panel de RRHH (Notificaciones y Horas Extra)[cite: 1]
def panel_rrhh(request):
    # Traemos las alertas que no han sido atendidas y las horas extra pendientes
    alertas_criticas = Alerta.objects.filter(atendida=False).order_by('-fecha_alerta')
    horas_pendientes = HorasExtra.objects.filter(estado='Pendiente').order_by('fecha')
    
    context = {
        'alertas': alertas_criticas,
        'horas_pendientes': horas_pendientes
    }
    return render(request, 'control_jornada/panel_rrhh.html', context)


#eiminar alerta y carga panel
def eliminar_alerta(request, id_alerta):
    alerta = get_object_or_404(Alerta, id_alerta=id_alerta)
    alerta.delete()
    return redirect('panel_rrhh')

# --- Función para bloquear/desbloquear mecánicos ---
def alternar_bloqueo(request, id_empleado):
    # Buscamos al empleado y alternamos su estado
    empleado = get_object_or_404(Empleado, id_empleado=id_empleado)
    empleado.bloqueado = not empleado.bloqueado
    empleado.save()
    return redirect('dashboard_jefatura')


# --- Función para validar al empleado en tiempo real ---
def verificar_empleado(request, documento):
    try:
        empleado = Empleado.objects.get(documento=documento)
        # Devolvemos un JSON diciendo si está bloqueado o no
        return JsonResponse({'existe': True, 'bloqueado': empleado.bloqueado})
    except Empleado.DoesNotExist:
        # Si no existe, también avisamos
        return JsonResponse({'existe': False, 'bloqueado': False})


