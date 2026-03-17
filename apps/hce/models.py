import uuid

from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, GeneratedField, Value


class HistoriaClinica(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.OneToOneField(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="historia_clinica",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "historias_clinicas"
        verbose_name = "Historia Clínica"
        verbose_name_plural = "Historias Clínicas"

    def __str__(self) -> str:
        return f"HCE — {self.paciente}"


class Consulta(models.Model):
    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        VIRTUAL = "virtual", "Virtual"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hce = models.ForeignKey(
        HistoriaClinica, on_delete=models.PROTECT, related_name="consultas"
    )
    cita = models.OneToOneField(
        "agenda.Cita",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consulta",
    )
    tipo_consulta = models.ForeignKey(
        "agenda.TipoConsulta", on_delete=models.PROTECT, related_name="consultas"
    )
    fecha_hora = models.DateTimeField()
    motivo_consulta = models.TextField()
    examen_fisico = models.JSONField(default=dict)
    plan_terapeutico = models.TextField(blank=True, default="")
    modalidad = models.CharField(
        max_length=20, choices=Modalidad.choices, default=Modalidad.PRESENCIAL
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        related_name="consultas_creadas",
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consultas"
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["hce", "-fecha_hora"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self) -> str:
        return f"Consulta {self.fecha_hora:%d/%m/%Y} — {self.hce.paciente}"


class SignosVitales(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consulta = models.OneToOneField(
        Consulta, on_delete=models.CASCADE, related_name="signos_vitales"
    )
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    talla_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    # PostgreSQL stored generated column — NULL when either input is NULL
    imc = GeneratedField(
        expression=ExpressionWrapper(
            F("peso_kg")
            / ((F("talla_cm") / Value(100.0)) * (F("talla_cm") / Value(100.0))),
            output_field=DecimalField(max_digits=5, decimal_places=2),
        ),
        output_field=DecimalField(max_digits=5, decimal_places=2, null=True),
        db_persist=True,
    )
    pa_sistolica = models.SmallIntegerField(null=True, blank=True)
    pa_diastolica = models.SmallIntegerField(null=True, blank=True)
    fc = models.SmallIntegerField(null=True, blank=True)  # frecuencia cardíaca (bpm)
    temperatura = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    saturacion_o2 = models.SmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "signos_vitales"
        verbose_name = "Signos Vitales"
        verbose_name_plural = "Signos Vitales"

    def __str__(self) -> str:
        return f"Signos Vitales — {self.consulta}"


class DiagnosticoConsulta(models.Model):
    class Tipo(models.TextChoices):
        PRINCIPAL = "principal", "Principal"
        SECUNDARIO = "secundario", "Secundario"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE, related_name="diagnosticos"
    )
    codigo_cie10 = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=300)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PRINCIPAL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "diagnosticos_consulta"
        verbose_name = "Diagnóstico de Consulta"
        verbose_name_plural = "Diagnósticos de Consulta"
        ordering = ["tipo", "codigo_cie10"]
        indexes = [
            models.Index(fields=["codigo_cie10"]),
            models.Index(fields=["consulta", "tipo"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo_cie10} — {self.descripcion} ({self.tipo})"


class MedicamentoPrescrito(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE, related_name="medicamentos"
    )
    nombre = models.CharField(max_length=200)
    presentacion = models.CharField(max_length=100)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    duracion = models.CharField(max_length=100)
    indicaciones = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medicamentos_prescritos"
        verbose_name = "Medicamento Prescrito"
        verbose_name_plural = "Medicamentos Prescritos"

    def __str__(self) -> str:
        return f"{self.nombre} {self.dosis} — {self.frecuencia}"
