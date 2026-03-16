import uuid

from django.db import models


class DocumentoGenerado(models.Model):
    class Tipo(models.TextChoices):
        RECETA = "receta", "Receta"
        CERTIFICADO = "certificado", "Certificado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consulta = models.ForeignKey(
        "hce.Consulta", on_delete=models.PROTECT, related_name="documentos"
    )
    paciente = models.ForeignKey(
        "pacientes.Paciente", on_delete=models.PROTECT, related_name="documentos"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    archivo_url = models.URLField(max_length=500)
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.PROTECT,
        related_name="documentos_generados",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documentos_generados"
        verbose_name = "Documento Generado"
        verbose_name_plural = "Documentos Generados"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.tipo} — {self.paciente} ({self.created_at:%d/%m/%Y})"
