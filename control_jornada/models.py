from django.db import models

class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento = models.CharField(max_length=30, unique=True)
    cargo = models.CharField(max_length=100)
    max_horas_semanales = models.DecimalField(max_digits=4, decimal_places=2, default=48.00)
    activo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'empleados'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class RegistroHoras(models.Model):
    id_registro = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='id_empleado')
    fecha = models.DateField(auto_now_add=True)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'registro_horas'

class HorasExtra(models.Model):
    id_hora_extra = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='id_empleado')
    id_registro = models.ForeignKey(RegistroHoras, on_delete=models.CASCADE, db_column='id_registro')
    horas_extra = models.DecimalField(max_digits=5, decimal_places=2)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, default='Pendiente')

    class Meta:
        managed = False
        db_table = 'horas_extra'

class Alerta(models.Model):
    id_alerta = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='id_empleado')
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    nivel_riesgo = models.CharField(max_length=20)
    mensaje = models.CharField(max_length=255)
    horas_acumuladas = models.DecimalField(max_digits=5, decimal_places=2)
    atendida = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'alertas'