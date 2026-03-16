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
