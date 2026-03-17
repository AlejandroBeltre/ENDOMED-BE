import uuid

from django.db import models


class Paciente(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    telefono_whatsapp = models.CharField(max_length=20)
    email = models.EmailField(blank=True, default="")
    sede = models.ForeignKey(
        "authentication.Sede", on_delete=models.PROTECT, related_name="pacientes"
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pacientes"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["cedula"]),
            models.Index(fields=["apellido", "nombre"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido} ({self.cedula})"


class ContactoEmergencia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="contactos_emergencia"
    )
    nombre = models.CharField(max_length=200)
    relacion = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contactos_emergencia"
        verbose_name = "Contacto de Emergencia"
        verbose_name_plural = "Contactos de Emergencia"

    def __str__(self) -> str:
        return f"{self.nombre} ({self.relacion}) — {self.paciente}"


class SeguroMedico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="seguros"
    )
    aseguradora = models.CharField(max_length=200)
    numero_poliza = models.CharField(max_length=100)
    cobertura = models.JSONField(default=dict, blank=True)
    vigencia_hasta = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "seguros_medicos"
        verbose_name = "Seguro Médico"
        verbose_name_plural = "Seguros Médicos"

    def __str__(self) -> str:
        return f"{self.aseguradora} ({self.numero_poliza}) — {self.paciente}"
