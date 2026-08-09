from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from .models import Empleado, RegistroHoras, Alerta, HorasExtra
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


# VISTA A: Dashboard de Alertas (Jefatura)
def dashboard_jefatura(request):
    # 1. Capturamos los filtros que el usuario seleccione en la interfaz
    cargo_seleccionado = request.GET.get('cargo', '')
    riesgo_seleccionado = request.GET.get('riesgo', '')

    with connection.cursor() as cursor:
        # 2. Obtenemos los contadores para los bloques superiores (Semáforo general)
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT e.id_empleado) as total_mecanicos,
                SUM(CASE WHEN COALESCE(t.horas_semana, 0) <= 40 THEN 1 ELSE 0 END) as normal,
                SUM(CASE WHEN COALESCE(t.horas_semana, 0) > 40 AND COALESCE(t.horas_semana, 0) <= 48 THEN 1 ELSE 0 END) as atencion,
                SUM(CASE WHEN COALESCE(t.horas_semana, 0) > 48 THEN 1 ELSE 0 END) as critico
            FROM empleados e
            LEFT JOIN (
                SELECT id_empleado, SUM(horas_trabajadas) as horas_semana 
                FROM registro_horas 
                WHERE fecha BETWEEN DATE_TRUNC('week', CURRENT_DATE)::DATE AND (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::DATE
                GROUP BY id_empleado
            ) t ON e.id_empleado = t.id_empleado;
        """)
        row_totales = cursor.fetchone()
        totales = {
            'mecanicos': row_totales[0] or 0,
            'normal': row_totales[1] or 0,
            'atencion': row_totales[2] or 0,
            'critico': row_totales[3] or 0,
        }

        # 3. Consulta principal para la tabla con filtros dinámicos
        query = """
            SELECT 
                e.id_empleado,
                e.nombre || ' ' || e.apellido AS mecanico,
                e.cargo,
                COALESCE(SUM(r.horas_trabajadas), 0) AS horas_semanales_acumuladas,
                e.max_horas_semanales,
                CASE 
                    WHEN COALESCE(SUM(r.horas_trabajadas), 0) > e.max_horas_semanales THEN 'Crítico'
                    WHEN COALESCE(SUM(r.horas_trabajadas), 0) >= 40 THEN 'Atención'
                    ELSE 'Normal'
                END AS nivel_riesgo,
                e.bloqueado
            FROM empleados e
            LEFT JOIN registro_horas r 
                ON e.id_empleado = r.id_empleado 
               AND r.fecha BETWEEN DATE_TRUNC('week', CURRENT_DATE)::DATE 
                                 AND (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::DATE
            WHERE 1=1
        """
        params = []

        # Aplicamos filtro de cargo si el usuario lo seleccionó
        if cargo_seleccionado:
            query += " AND e.cargo = %s"
            params.append(cargo_seleccionado)

        query += " GROUP BY e.id_empleado, e.nombre, e.apellido, e.cargo, e.max_horas_semanales, e.bloqueado"

        # Filtro por nivel de riesgo (se aplica sobre el resultado agrupado usando HAVING)
        if riesgo_seleccionado:
            if riesgo_seleccionado == 'Normal':
                query += " HAVING COALESCE(SUM(r.horas_trabajadas), 0) < 40"
            elif riesgo_seleccionado == 'Atención':
                query += " HAVING COALESCE(SUM(r.horas_trabajadas), 0) >= 40 AND COALESCE(SUM(r.horas_trabajadas), 0) <= 48"
            elif riesgo_seleccionado == 'Crítico':
                query += " HAVING COALESCE(SUM(r.horas_trabajadas), 0) > 48"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        # Obtenemos la lista de cargos únicos para poblar el menú desplegable del filtro
        cursor.execute("SELECT DISTINCT cargo FROM empleados")
        cargos_disponibles = [row[0] for row in cursor.fetchall()]

    context = {
        'totales': totales,
        'empleados': resultados,
        'cargos': cargos_disponibles,
        'cargo_actual': cargo_seleccionado,
        'riesgo_actual': riesgo_seleccionado,
    }
    
    return render(request, 'control_jornada/dashboard.html', context)


# VISTA B: Módulo de Registro de Turno (Mecánico)
def registro_turno(request):
    if request.method == 'POST':
        documento_texto = request.POST.get('documento_empleado')
        hora_entrada = request.POST.get('hora_entrada')
        hora_salida = request.POST.get('hora_salida')
        horas_trabajadas = request.POST.get('horas_trabajadas')

        try:
            empleado = Empleado.objects.get(documento=documento_texto)
            
            RegistroHoras.objects.create(
                id_empleado=empleado,
                fecha=datetime.now().date(),
                hora_entrada=hora_entrada,
                hora_salida=hora_salida,
                horas_trabajadas=horas_trabajadas
            )
            return redirect('dashboard_jefatura')
            
        except Empleado.DoesNotExist:
            context = {'error': 'No se encontró un empleado con ese documento.'}
            return render(request, 'control_jornada/registro_turno.html', context)

    return render(request, 'control_jornada/registro_turno.html')


# VISTA C: Panel de RRHH (Notificaciones y Horas Extra)
def panel_rrhh(request):
    alertas_criticas = Alerta.objects.filter(atendida=False).order_by('-fecha_alerta')
    horas_pendientes = HorasExtra.objects.filter(estado='Pendiente').order_by('fecha')
    
    context = {
        'alertas': alertas_criticas,
        'horas_pendientes': horas_pendientes
    }
    return render(request, 'control_jornada/panel_rrhh.html', context)


# Eliminar alerta y carga panel
def eliminar_alerta(request, id_alerta):
    alerta = get_object_or_404(Alerta, id_alerta=id_alerta)
    alerta.delete()
    return redirect('panel_rrhh')


# --- Función para bloquear/desbloquear mecánicos ---
def alternar_bloqueo(request, id_empleado):
    empleado = get_object_or_404(Empleado, id_empleado=id_empleado)
    empleado.bloqueado = not empleado.bloqueado
    empleado.save()
    return redirect('dashboard_jefatura')


# --- Función para validar al empleado en tiempo real ---
def verificar_empleado(request, documento):
    try:
        empleado = Empleado.objects.get(documento=documento)
        return JsonResponse({'existe': True, 'bloqueado': empleado.bloqueado})
    except Empleado.DoesNotExist:
        return JsonResponse({'existe': False, 'bloqueado': False})

#funcion para visitar el perfil mecanico

def perfil_mecanico(request, id_empleado):
    empleado = get_object_or_404(Empleado, id_empleado=id_empleado)
    
    with connection.cursor() as cursor:
        # 1. Total de horas acumuladas en la semana actual
        cursor.execute("""
            SELECT COALESCE(SUM(horas_trabajadas), 0)
            FROM registro_horas
            WHERE id_empleado = %s
              AND fecha BETWEEN DATE_TRUNC('week', CURRENT_DATE)::DATE 
                            AND (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::DATE
        """, [id_empleado])
        row_horas = cursor.fetchone()
        horas_acumuladas = row_horas[0] if row_horas else 0

        # 2. Historial detallado de jornadas de este empleado
        cursor.execute("""
            SELECT fecha, hora_entrada, hora_salida, horas_trabajadas
            FROM registro_horas
            WHERE id_empleado = %s
            ORDER BY fecha DESC, hora_entrada DESC
            LIMIT 10
        """, [id_empleado])
        historial = cursor.fetchall()

    # Determinamos el estado de riesgo dinámico
    max_horas = empleado.max_horas_semanales
    if horas_acumuladas > max_horas:
        estado_riesgo = "Crítico"
    elif horas_acumuladas >= (max_horas - 2):
        estado_riesgo = "Atención"
    else:
        estado_riesgo = "Normal"

    context = {
        'empleado': empleado,
        'horas_acumuladas': horas_acumuladas,
        'max_horas': max_horas,
        'estado_riesgo': estado_riesgo,
        'historial': historial,
    }
    return render(request, 'control_jornada/perfil_mecanico.html', context)