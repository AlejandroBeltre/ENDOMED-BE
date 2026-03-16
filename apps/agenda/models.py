import uuid

from django.db import models


class TipoConsulta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    duracion_min = models.PositiveSmallIntegerField()
    tarifa_rd = models.DecimalField(max_digits=10, decimal_places=2)
    color_hex = models.CharField(max_length=7)  # "#RRGGBB"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tipos_consulta"
        verbose_name = "Tipo de Consulta"
        verbose_name_plural = "Tipos de Consulta"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Cita(models.Model):
    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        VIRTUAL = "virtual", "Virtual"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"
        COMPLETADA = "completada", "Completada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        "pacientes.Paciente", on_delete=models.PROTECT, related_name="citas"
    )
    sede = models.ForeignKey(
        "authentication.Sede", on_delete=models.PROTECT, related_name="citas"
    )
    profesional = models.ForeignKey(
        "authentication.User", on_delete=models.PROTECT, related_name="citas"
    )
    tipo_consulta = models.ForeignKey(
        TipoConsulta, on_delete=models.PROTECT, related_name="citas"
    )
    fecha_hora = models.DateTimeField()
    duracion_min = models.PositiveSmallIntegerField()
    modalidad = models.CharField(
        max_length=20, choices=Modalidad.choices, default=Modalidad.PRESENCIAL
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    notas_previas = models.TextField(blank=True, default="")
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "citas"
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ["fecha_hora"]
        indexes = [
            models.Index(fields=["fecha_hora", "sede"]),
            models.Index(fields=["profesional", "fecha_hora"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.paciente} — {self.fecha_hora:%d/%m/%Y %H:%M}"
